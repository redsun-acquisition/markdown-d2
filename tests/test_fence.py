"""Turning d2 blocks into figures."""

from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path

import pytest
from pymdownx.superfences import SuperFencesException

ICON = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
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

    assert html.count('<figure class="d2"') == 2
    assert 'aria-label="Build steps"' in html
    assert "<figcaption>Build steps</figcaption>" in html
    assert html.count('class="d2-board"') == 4
    assert 'data-name="steps.1"' in html and 'data-name="steps.2"' in html
    assert html.count('class="d2-light"') == 4 and html.count('class="d2-dark"') == 4
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

    assert html.count('<figure class="d2"') == 2


def test_render_an_empty_block(page: Callable[..., str]) -> None:
    """Render an empty block as a figure with one board."""
    html = page("```d2\n```")

    assert html.count('class="d2-board"') == 1


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

    assert '<div class="d2-error" role="alert">' in html
    assert "connection missing destination" in html


def test_stop_when_node_is_missing(page: Callable[..., str], files: Path) -> None:
    """Raise, naming the diagram, when the Node program does not exist."""
    with pytest.raises(SuperFencesException, match='diagram starting "a"'):
        page("```d2\na\n```", node=files / "no-such-node")
