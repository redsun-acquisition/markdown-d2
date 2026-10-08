"""The superfences formatter and validator for d2 blocks."""

from __future__ import annotations

import contextlib
import functools
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pymdownx.superfences import SuperFencesException

from ._cache import Cache, key
from ._paths import ASSETS, VERSION, d2_version, default_node
from ._renderer import Board, D2Error, Renderer, RendererError, node_command
from ._sources import SourceError, prepare

if TYPE_CHECKING:
    from markdown import Markdown

OPTIONS = {"title", "transition"}
TRANSITIONS = ("none", "fade", "morph")
D2_POSITION = re.compile(r"^index\.d2:(\d+):(\d+):(.*)$", re.DOTALL)
VIEW_BOX = re.compile(r'^<svg (?![^>]*\bwidth=)([^>]*?)viewBox="0 0 ([\d.]+) ([\d.]+)"')
ID = re.compile(r'\bid="([^"]+)"')


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
    transition: str
    """How the picture changes from one step to the next."""


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
        page = zensical_page(md)
        try:
            boards = render_boards(
                source, options, settings, self._renderer, self._versions
            )
        except (D2Error, SourceError, RendererError, ValueError, OSError) as error:
            where = f"{page.path}: " if page is not None else ""
            message = (
                f"markdown-d2: {where}{block_name(source, options)}: {describe(error)}"
            )
            if settings.errors == "show":
                return (
                    '<div class="markdown-d2-error" role="alert">'
                    f"<pre>{html.escape(message)}</pre></div>"
                )
            raise SuperFencesException(message) from error
        parts = []
        for step, board in enumerate(boards, start=1):
            text = (
                f'<p class="markdown-d2-text">{html.escape(board.label)}</p>'
                if board.label
                else ""
            )
            parts.append(
                f'<div class="markdown-d2-board" data-step="{step}" '
                f'data-name="{html.escape(board.name)}">{text}'
                f'<div class="markdown-d2-light">{unique_ids(board.light, md)}</div>'
                f'<div class="markdown-d2-dark">{unique_ids(board.dark, md)}</div>'
                "</div>"
            )
        title = options.get("title")
        label = f' aria-label="{html.escape(title)}"' if title else ""
        caption = f"<figcaption>{html.escape(title)}</figcaption>" if title else ""
        transition = options.get("transition", settings.transition)
        figure = (
            f'<figure class="markdown-d2" data-transition="{transition}"{label}>'
            f"{''.join(parts)}{caption}</figure>"
        )
        return assets_once(page, settings) + figure


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
    transition: Literal["none", "fade", "morph"] = "fade",
) -> Formatter:
    """Return the function that turns a d2 block into a figure.

    Parameters
    ----------
    root
        Folder that imports and icon paths are relative to.
    cache_dir
        Folder that keeps rendered SVGs between builds; `None` keeps nothing.
    light_theme
        D2 theme ID of the light picture; a diagram's own `theme-id` wins.
    dark_theme
        D2 theme ID of the dark picture; a diagram's own `dark-theme-id` wins.
    dark_selector
        CSS selector of the page element that marks the dark theme.
    errors
        `"raise"` stops the build on a broken block; `"show"` draws the error
        in place of the diagram.
    timeout
        Seconds to wait for one diagram, every board in both themes.
    node
        Node program to run; by default the one `nodejs-wheel-binaries`
        installed.
    transition
        How a diagram with several steps changes from one to the next:
        `"none"` switches at once, `"fade"` fades the new step in, and
        `"morph"` moves each shape the two steps share to its new place and
        fades in the rest. A block's own `transition` option wins.

    Raises
    ------
    ValueError
        If *transition* is not one of those three.
    """
    if transition not in TRANSITIONS:
        raise ValueError(unknown_transition(transition))
    settings = Settings(
        root=Path(root),
        cache=Cache(None if cache_dir is None else Path(cache_dir)),
        light_theme=light_theme,
        dark_theme=dark_theme,
        dark_selector=dark_selector,
        errors=errors,
        transition=transition,
    )
    command = node_command(Path(node) if node else default_node())
    return Formatter(settings, command, timeout)


def unknown_transition(name: str) -> str:
    """Return the message for a transition that does not exist."""
    return f'unknown transition "{name}"; use none, fade or morph'


def block_name(source: str, options: dict[str, Any]) -> str:
    """Return how errors name a block: its title, or its first line."""
    if "title" in options:
        return f'diagram "{options["title"]}"'
    first = next((line.strip() for line in source.splitlines() if line.strip()), "")
    return f'diagram starting "{first}"'


def zensical_page(md: Markdown) -> Any:
    """Return the page Zensical is rendering, or `None` outside Zensical."""
    if "rendering_context" not in md.preprocessors:
        return None
    return getattr(md.preprocessors["rendering_context"], "page", None)


def describe(error: Exception) -> str:
    """Return *error* as the build reports it, D2 positions as line and column."""
    match error:
        case D2Error(messages=messages):
            return "; ".join(position(message) for message in messages)
        case _:
            return str(error)


def position(message: str) -> str:
    """Turn `index.d2:4:3: text` into `line 4, column 3: text`."""
    match = D2_POSITION.match(message)
    if match is None:
        return message
    line, column, text = match.groups()
    return f"line {line}, column {column}:{text}"


def render_boards(
    source: str,
    options: dict[str, Any],
    settings: Settings,
    renderer: Renderer,
    versions: tuple[str, str],
) -> list[Board]:
    """Return each board of one block, its SVGs sized to their view box.

    Raises
    ------
    ValueError
        If the block has an option other than `title` and `transition`, or
        an unknown transition.
    """
    unknown = sorted(set(options) - OPTIONS)
    if unknown:
        raise ValueError(f'unknown option "{unknown[0]}"; set it in d2-config instead')
    if options.get("transition", settings.transition) not in TRANSITIONS:
        raise ValueError(unknown_transition(options["transition"]))
    files = prepare(source, settings.root)
    name = key(files, settings.light_theme, settings.dark_theme, *versions)
    cached = settings.cache.get(f"{name}.json")
    boards = read_boards(cached) if cached is not None else None
    if boards is None:
        boards = renderer.draw(
            files, settings.light_theme, settings.dark_theme, name[:12]
        )
        settings.cache.put(f"{name}.json", json.dumps(boards))
    return [
        board._replace(light=sized(board.light), dark=sized(board.dark))
        for board in boards
    ]


def read_boards(text: str) -> list[Board] | None:
    """Return the boards a cache entry holds, or `None` for an entry of another shape."""
    try:
        return [Board(*board) for board in json.loads(text)]
    except (TypeError, ValueError):
        return None


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


def unique_ids(svg: str, md: Markdown) -> str:
    """Return *svg* with a suffix on every id and reference to it.

    The suffix counts the SVGs *md* has produced, so no two SVGs on one page
    share an id, which would make a gradient or an arrowhead point into a
    hidden copy.
    """
    ids = set(ID.findall(svg))
    if not ids:
        return svg
    count = getattr(md, "markdown_d2_svgs", 0) + 1
    md.markdown_d2_svgs = count  # type: ignore[attr-defined]
    names = "|".join(re.escape(name) for name in sorted(ids, key=len, reverse=True))
    pattern = re.compile(rf"""(\bid="|url\(["']?#|href="#)({names})(?=["')])""")
    return pattern.sub(lambda match: f"{match[1]}{match[2]}-{count}", svg)


@functools.cache
def assets(dark_selector: str) -> str:
    """Return the inline CSS and script of the figures."""
    css = (ASSETS / "d2.css").read_text(encoding="utf-8")
    script = (ASSETS / "d2.js").read_text(encoding="utf-8")
    return (
        f"<style data-markdown-d2>{css.replace('DARK_SELECTOR', dark_selector)}</style>"
        f"<script data-markdown-d2>{script}</script>"
    )


def assets_once(page: Any, settings: Settings) -> str:
    """Return the inline CSS and script, once per Zensical page.

    Outside Zensical there is no page to mark, so every figure carries them
    and the script sets itself up once.
    """
    # Zensical makes a new page object for every render, so a mark on it
    # resets when `zensical serve` renders the page again
    if page is not None:
        if getattr(page, "markdown_d2_assets", False):
            return ""
        with contextlib.suppress(AttributeError):
            page.markdown_d2_assets = True
    return assets(settings.dark_selector)
