"""Turning d2 blocks into figures."""

from __future__ import annotations

import base64
import json
import pickle
import re
from collections.abc import Callable
from pathlib import Path

import markdown
import pytest
from pymdownx.superfences import SuperFencesException

from markdown_d2 import formatter
from markdown_d2._fence import describe
from markdown_d2._paths import VERSION, d2_version
from markdown_d2._renderer import D2Error

ICON = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
GRADIENT = """```d2
a: { style.fill: "linear-gradient(red, blue)"; style.shadow: true }
a -> b
steps: { 1: { c } }
```"""
PAGE = """
```d2 title="Build steps"
svc_board
steps: {
  1: { dev_board }
  2: { view_board }
}
```

```d2
stage: @parts/stage
cam: { icon: icons/camera.svg }
```
"""


@pytest.fixture
def files(tmp_path: Path) -> Path:
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "stage.d2").write_text("motor_shape\n", encoding="utf-8")
    (tmp_path / "icons").mkdir()
    (tmp_path / "icons" / "camera.svg").write_bytes(ICON)
    return tmp_path


def test_render_a_page_then_serve_it_from_the_cache(
    page: Callable[..., str], files: Path
) -> None:
    """Render boards in both themes, then rebuild without Node from the cache."""
    html = page(PAGE)
    again = page(PAGE, node=files / "no-such-node")

    assert html.count('<figure class="markdown-d2"') == 2
    assert 'aria-label="Build steps"' in html
    assert "<figcaption>Build steps</figcaption>" in html
    assert html.count('class="markdown-d2-board"') == 4
    assert 'data-name="steps.1"' in html and 'data-name="steps.2"' in html
    assert (
        html.count('class="markdown-d2-light"') == 4
        and html.count('class="markdown-d2-dark"') == 4
    )
    assert "view_board" in html and "motor_shape" in html
    assert "data:image/svg+xml;base64," + base64.b64encode(ICON).decode() in html
    assert html.count("<style data-markdown-d2>") == 2
    assert html.count("<script data-markdown-d2>") == 2
    assert again == html


def test_give_the_same_input_the_same_output(page: Callable[..., str]) -> None:
    """Produce byte-identical HTML for the same block without a cache."""
    first = page("```d2\na -> b\n```", cache_dir=None)
    second = page("```d2\na -> b\n```", cache_dir=None)

    assert first == second


def test_render_the_same_diagram_twice_on_a_page(page: Callable[..., str]) -> None:
    """Give a page two figures when it holds the same block twice."""
    html = page("```d2\na -> b\n```\n\n```d2\na -> b\n```")

    assert html.count('<figure class="markdown-d2"') == 2


def test_render_an_empty_block(page: Callable[..., str]) -> None:
    """Render an empty block as a figure with one board."""
    html = page("```d2\n```")

    assert html.count('class="markdown-d2-board"') == 1


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            '```d2 title="Broken"\na -> \n```',
            'markdown-d2: diagram "Broken": line 1, column 1: connection missing destination',
        ),
        (
            "```d2\nx: @nowhere\n```",
            r'markdown-d2: diagram starting "x: @nowhere": .*nowhere\.d2',
        ),
        (
            '```d2 layout="elk"\na\n```',
            'markdown-d2: diagram starting "a": unknown option "layout"; set it in d2-config instead',
        ),
        (
            "```d2\na: { icon: https://example.org/a.svg }\n```",
            "URL icons are not enabled",
        ),
        (
            '```d2 transition="spin"\na\n```',
            'unknown transition "spin"; use none, fade or morph',
        ),
    ],
)
def test_stop_the_build_on_a_broken_block(
    page: Callable[..., str], text: str, message: str
) -> None:
    """Raise `SuperFencesException`, naming the diagram, for each kind of mistake."""
    with pytest.raises(SuperFencesException, match=message):
        page(text)


def test_show_errors_in_the_page_when_asked(page: Callable[..., str]) -> None:
    """Draw the error in place of the diagram with `errors="show"`."""
    html = page("```d2\na -> \n```", errors="show")

    assert '<div class="markdown-d2-error" role="alert">' in html
    assert "connection missing destination" in html


def test_stop_when_node_is_missing(page: Callable[..., str], files: Path) -> None:
    """Raise, naming the diagram, when the Node program does not exist."""
    with pytest.raises(SuperFencesException, match='diagram starting "a"'):
        page("```d2\na\n```", node=files / "no-such-node")


def test_survive_pickling(tmp_path: Path) -> None:
    """Pickle the formatter, as Zensical does with its settings, and still render."""
    copy = pickle.loads(pickle.dumps(formatter(root=tmp_path, cache_dir=None)))

    html = markdown.Markdown(
        extensions=["pymdownx.superfences"],
        extension_configs={
            "pymdownx.superfences": {
                "custom_fences": [{"name": "d2", "class": "d2", "format": copy}]
            }
        },
    ).convert("```d2\na -> b\n```")

    assert html.count('<figure class="markdown-d2"') == 1


def test_give_each_picture_its_natural_size(page: Callable[..., str]) -> None:
    """Size each SVG from its view box, so a theme that shrinks figures can't."""
    html = page("```d2\na -> b\n```")

    sizes = re.findall(
        r'<div class="markdown-d2-light"><svg [^>]*?width="(\d+)" height="(\d+)"', html
    )
    assert sizes and all(int(width) > 0 and int(height) > 0 for width, height in sizes)


def test_carry_the_versions_in_the_pickle() -> None:
    """Put both versions in the pickle, so Zensical re-renders after an upgrade."""
    pickled = pickle.dumps(formatter(cache_dir=None))

    assert d2_version().encode() in pickled
    assert VERSION.encode() in pickled


def test_give_every_svg_its_own_ids(page: Callable[..., str]) -> None:
    """Make ids unique across copies, themes and boards, with references kept."""
    html = page(f"{GRADIENT}\n\n{GRADIENT}")

    ids = re.findall(r'\bid="([^"]+)"', html)
    references = re.findall(r'(?:url\(#|href="#)([^")]+)', html)
    assert len(ids) == len(set(ids))
    assert references and set(references) <= set(ids)


def test_stop_when_the_cache_cannot_be_written(
    page: Callable[..., str], tmp_path: Path
) -> None:
    """Raise, naming the diagram, when the cache folder is a file."""
    (tmp_path / "taken").write_text("", encoding="utf-8")

    with pytest.raises(SuperFencesException, match='diagram starting "a"'):
        page("```d2\na\n```", cache_dir=tmp_path / "taken")


def test_keep_a_d2_message_without_a_position() -> None:
    """Report a D2 message that names the file but no line as it is."""
    assert describe(D2Error(["index.d2: odd"])) == "index.d2: odd"


@pytest.mark.parametrize(
    ("text", "settings", "transition"),
    [
        ("```d2\na\n```", {}, "fade"),
        ("```d2\na\n```", {"transition": "none"}, "none"),
        ('```d2 transition="morph"\na\n```', {"transition": "none"}, "morph"),
    ],
)
def test_mark_the_transition_between_steps(
    page: Callable[..., str], text: str, settings: dict[str, str], transition: str
) -> None:
    """Take the transition from the block, else the formatter, else fade."""
    html = page(text, **settings)

    assert f'<figure class="markdown-d2" data-transition="{transition}">' in html


def test_show_each_boards_label_above_it(page: Callable[..., str]) -> None:
    """Put a board's label, escaped, above its pictures and leave unlabeled boards bare."""
    html = page('```d2\nlabel: "first <step>"\na\nsteps: {\n  1: { b }\n}\n```')

    text = '<p class="markdown-d2-text">first &lt;step&gt;</p>'
    assert text in html
    assert html.index(text) < html.index('class="markdown-d2-light"')
    assert html.count('class="markdown-d2-text"') == 1


def test_draw_again_over_a_cache_entry_of_another_shape(
    page: Callable[..., str], tmp_path: Path
) -> None:
    """Treat a cache entry an older version wrote as missing, and draw again."""
    page("```d2\na -> b\n```")
    for entry in (tmp_path / "cache").glob("*.json"):
        boards = json.loads(entry.read_text(encoding="utf-8"))
        entry.write_text(json.dumps([board[:3] for board in boards]), encoding="utf-8")

    html = page("```d2\na -> b\n```")

    assert html.count('<figure class="markdown-d2"') == 1


def test_scope_each_pictures_style_to_it(page: Callable[..., str]) -> None:
    """Prefix the code block rules of each picture with that picture's class."""
    html = page("```d2\ncode: |cpp\n  s = load(seq);\n|\n```")

    roots = re.findall(r'<svg [^>]*class="(d2-[0-9]+)', html)
    scopes = re.findall(r"[.](d2-[0-9]+) +[.](?:light|dark)-code *[{]", html)
    assert len(roots) == 2
    assert scopes == [roots[0], roots[0], roots[1], roots[1]]
    assert not re.search(r"[}\[] *[.](?:light|dark)-code *[{]", html)
