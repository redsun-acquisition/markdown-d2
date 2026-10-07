"""The superfences formatter and validator for d2 blocks."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pymdownx.superfences import SuperFencesException

from ._cache import Cache, key
from ._paths import ASSETS, VERSION, d2_version, default_node
from ._renderer import D2Error, Renderer, RendererError, node_command
from ._sources import SourceError, prepare

if TYPE_CHECKING:
    from markdown import Markdown

VARIANTS: tuple[Literal["light"], Literal["dark"]] = ("light", "dark")
OPTIONS = {"title"}
D2_POSITION = "index.d2:"
VIEW_BOX = re.compile(r'^<svg (?![^>]*\bwidth=)([^>]*?)viewBox="0 0 ([\d.]+) ([\d.]+)"')


@dataclass(frozen=True)
class Settings:
    """The settings of one formatter."""

    root: Path
    """Folder that imports and icons are looked up in."""
    cache: Cache
    """Where rendered SVGs and board lists are kept."""
    light_theme: int
    """D2 theme ID of the light SVG."""
    dark_theme: int
    """D2 theme ID of the dark SVG."""
    dark_selector: str
    """CSS selector under which the dark SVG shows."""
    errors: Literal["raise", "show"]
    """Whether a broken block stops the build or is drawn in the page."""


class Formatter:
    """What `pymdownx.superfences` calls for each d2 block.

    It can be pickled, as Zensical does with its settings; the copy starts its
    own render process when it first needs one. The pickle carries the package
    and D2 versions, so a tool that caches pages by the pickled settings
    renders them again after an upgrade.
    """

    def __init__(self, settings: Settings, command: list[str], timeout: float) -> None:
        self._settings = settings
        self._command = command
        self._timeout = timeout
        self._versions = (VERSION, d2_version())
        self._renderer: Renderer | None = None

    def __getstate__(self) -> dict[str, Any]:
        """Return the settings, leaving out the render process."""
        return {**self.__dict__, "_renderer": None}

    def __call__(
        self,
        source: str,
        language: str,
        class_name: str,
        options: dict[str, Any],
        md: Markdown,
        **kwargs: Any,
    ) -> str:
        """Return the figure of one block, or its error when errors are shown.

        Raises
        ------
        SuperFencesException
            If the block cannot be drawn and errors are raised.
        """
        if self._renderer is None:
            self._renderer = Renderer(self._command, self._timeout)
        settings = self._settings
        name = block_name(source, options)
        page = page_path(md)
        try:
            figure = render_figure(source, options, settings, self._renderer)
        except (D2Error, SourceError, RendererError, ValueError) as error:
            message = (
                f"markdown-d2: {page + ': ' if page else ''}{name}: {describe(error)}"
            )
            if settings.errors == "show":
                return f'<div class="markdown-d2-error" role="alert"><pre>{html.escape(message)}</pre></div>'
            raise SuperFencesException(message) from error
        return assets_once(md, settings) + figure


def validator(
    language: str,
    inputs: dict[str, str],
    options: dict[str, Any],
    attrs: dict[str, Any],
    md: Markdown,
) -> bool:
    """Accept every option of a d2 block; the formatter checks them."""
    options.update(inputs)
    return True


def formatter(
    *,
    root: str | Path = ".",
    cache_dir: str | Path | None = ".cache/markdown-d2",
    light_theme: int = 0,
    dark_theme: int = 200,
    dark_selector: str = '[data-md-color-scheme="slate"]',
    errors: Literal["raise", "show"] = "raise",
    timeout: float = 60,
    node: str | Path | None = None,
) -> Formatter:
    """Return the function that turns a d2 block into a figure.

    Parameters
    ----------
    root
        Folder that imports and icon paths are relative to.
    cache_dir
        Folder that keeps rendered SVGs between builds; `None` keeps nothing.
    light_theme, dark_theme
        D2 theme IDs; a diagram's own `theme-id` and `dark-theme-id` win.
    dark_selector
        CSS selector of the page element that marks the dark theme.
    errors
        `"raise"` stops the build on a broken block; `"show"` draws the error
        in place of the diagram.
    timeout
        Seconds to wait for one SVG.
    node
        Node program to run; by default the one `nodejs-wheel-binaries`
        installed.
    """
    settings = Settings(
        root=Path(root),
        cache=Cache(None if cache_dir is None else Path(cache_dir)),
        light_theme=light_theme,
        dark_theme=dark_theme,
        dark_selector=dark_selector,
        errors=errors,
    )
    command = node_command(Path(node) if node else default_node())
    return Formatter(settings, command, timeout)


def block_name(source: str, options: dict[str, Any]) -> str:
    """Return how errors name a block: its title, or its first line."""
    if "title" in options:
        return f'diagram "{options["title"]}"'
    first = next((line.strip() for line in source.splitlines() if line.strip()), "")
    return f'diagram starting "{first}"'


def page_path(md: Markdown) -> str | None:
    """Return the page Zensical is rendering, or `None` outside Zensical."""
    if "rendering_context" not in md.preprocessors:
        return None
    page = getattr(md.preprocessors["rendering_context"], "page", None)
    return getattr(page, "path", None)


def describe(error: Exception) -> str:
    """Return *error* as the build reports it, D2 positions as line and column."""
    match error:
        case D2Error(messages=messages):
            return "; ".join(position(message) for message in messages)
        case _:
            return str(error)


def position(message: str) -> str:
    """Turn `index.d2:4:3: text` into `line 4, column 3: text`."""
    if not message.startswith(D2_POSITION):
        return message
    line, column, text = message.removeprefix(D2_POSITION).split(":", 2)
    return f"line {line}, column {column}:{text}"


def render_figure(
    source: str, options: dict[str, Any], settings: Settings, renderer: Renderer
) -> str:
    """Return the figure of one block.

    Raises
    ------
    ValueError
        If the block has an option other than `title`.
    """
    unknown = sorted(set(options) - OPTIONS)
    if unknown:
        raise ValueError(f'unknown option "{unknown[0]}"; set it in d2-config instead')
    files = prepare(source, settings.root)
    versions = (d2_version(), VERSION)
    source_key = key(files, *versions)
    listed = settings.cache.get(f"{source_key}.boards.json")
    if listed is None:
        boards = renderer.boards(files)
        settings.cache.put(f"{source_key}.boards.json", json.dumps(boards))
    else:
        boards = json.loads(listed)
    parts = []
    for step, board in enumerate(boards, start=1):
        svgs = {}
        for variant in VARIANTS:
            theme = settings.light_theme if variant == "light" else settings.dark_theme
            name = key(files, board, variant, theme, *versions)
            svg = settings.cache.get(f"{name}.svg")
            if svg is None:
                svg = renderer.render(
                    files,
                    board,
                    variant,
                    settings.light_theme,
                    settings.dark_theme,
                    name[:12],
                )
                settings.cache.put(f"{name}.svg", svg)
            svgs[variant] = sized(svg)
        parts.append(
            f'<div class="markdown-d2-board" data-step="{step}" data-name="{html.escape(board)}">'
            f'<div class="markdown-d2-light">{svgs["light"]}</div>'
            f'<div class="markdown-d2-dark">{svgs["dark"]}</div></div>'
        )
    title = options.get("title")
    label = f' aria-label="{html.escape(title)}"' if title else ""
    caption = f"<figcaption>{html.escape(title)}</figcaption>" if title else ""
    return f'<figure class="markdown-d2"{label}>{"".join(parts)}{caption}</figure>'


def sized(svg: str) -> str:
    """Return *svg* with a width and height taken from its view box.

    D2 sizes its outer SVG by the view box alone, which collapses inside a
    figure that a theme shrinks to fit its content.
    """

    def add_size(match: re.Match[str]) -> str:
        attributes, width, height = match.groups()
        return (
            f'<svg {attributes}width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"'
        )

    return VIEW_BOX.sub(add_size, svg, count=1)


def assets_once(md: Markdown, settings: Settings) -> str:
    """Return the inline CSS and script, once per Zensical page.

    Outside Zensical there is no page to mark, so every figure carries them
    and the script sets itself up once.
    """
    css = (ASSETS / "d2.css").read_text(encoding="utf-8")
    css = css.replace("DARK_SELECTOR", settings.dark_selector)
    script = (ASSETS / "d2.js").read_text(encoding="utf-8")
    tags = (
        f"<style data-markdown-d2>{css}</style>"
        f"<script data-markdown-d2>{script}</script>"
    )
    if "rendering_context" not in md.preprocessors:
        return tags
    page = getattr(md.preprocessors["rendering_context"], "page", None)
    if page is None:
        return tags
    # Zensical makes a new page object for every render, so a mark on it
    # resets when `zensical serve` renders the page again
    if getattr(page, "markdown_d2_assets", False):
        return ""
    try:
        page.markdown_d2_assets = True
    except AttributeError:
        return tags
    return tags
