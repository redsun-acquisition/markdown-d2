"""The Node process that renders diagrams."""

from __future__ import annotations

import sys
import threading
from collections.abc import Generator
from pathlib import Path

import pytest

from markdown_d2._paths import default_node
from markdown_d2._renderer import Board, D2Error, Renderer, RendererError, node_command
from markdown_d2._sources import prepare

STAND_INS = Path(__file__).parent / "stand_ins"
STEPS = "alpha_top\nsteps: {\n  1: { beta_first }\n  2: { gamma_second }\n}\n"


@pytest.fixture
def renderer() -> Generator[Renderer, None, None]:
    instance = Renderer(node_command(default_node()), timeout=60)
    yield instance
    instance.close()


def test_draw_every_board_in_both_themes(renderer: Renderer) -> None:
    """Draw the top board and each step, light and dark, in one request."""
    boards = renderer.draw({"index.d2": STEPS}, 0, 200, "s")

    assert [board.name for board in boards] == ["", "steps.1", "steps.2"]
    assert "alpha_top" in boards[0].light and "beta_first" not in boards[0].light
    assert "gamma_second" in boards[2].dark
    assert "#1E1E2E" in boards[2].dark and "#1E1E2E" not in boards[2].light
    assert "prefers-color-scheme" not in boards[2].dark


def test_draw_a_board_whose_name_has_a_dot(renderer: Renderer) -> None:
    """Quote a board name that D2 would otherwise split at its dot."""
    boards = renderer.draw(
        {"index.d2": 'a\nlayers: { "v1.2": { inner } }\n'}, 0, 200, "s"
    )

    assert boards[1] == Board('layers."v1.2"', boards[1].light, boards[1].dark)
    assert "inner" in boards[1].light


def test_keep_text_that_is_not_ascii(renderer: Renderer) -> None:
    """Carry a label with non-ASCII text through the pipe unchanged."""
    source = "s: stage (µm)\na: Ångström\ns -> a\n"
    svg = renderer.draw({"index.d2": source}, 0, 200, "s")[0].light

    assert "stage (µm)" in svg
    assert "Ångström" in svg


def test_answer_two_threads_with_their_own_svgs(renderer: Renderer) -> None:
    """Give each of two concurrent callers the SVG of its own diagram."""
    results: dict[str, str] = {}

    def work(label: str) -> None:
        results[label] = renderer.draw({"index.d2": label}, 0, 200, label)[0].light

    labels = ("alpha_label", "beta_label")
    threads = [threading.Thread(target=work, args=(label,)) for label in labels]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert "alpha_label" in results["alpha_label"]
    assert "beta_label" not in results["alpha_label"]
    assert "beta_label" in results["beta_label"]
    assert "alpha_label" not in results["beta_label"]


def test_report_each_d2_error(renderer: Renderer) -> None:
    """Raise every compile error D2 reports, with its position."""
    with pytest.raises(D2Error) as caught:
        renderer.draw({"index.d2": "a -> \n b: {"}, 0, 200, "s")

    assert caught.value.messages == [
        "index.d2:1:1: connection missing destination",
        "index.d2:2:5: maps must be terminated with }",
    ]


def test_restart_node_once_after_a_crash(tmp_path: Path) -> None:
    """Restart a process that died, and answer from the new one."""
    command = [sys.executable, str(STAND_INS / "dies_once.py"), str(tmp_path / "flag")]
    instance = Renderer(command, timeout=10)

    assert instance.draw({"index.d2": "a"}, 0, 200, "s") == [
        Board("", "<svg/>", "<svg/>")
    ]
    instance.close()


def test_raise_when_node_dies_twice() -> None:
    """Raise with the process's own output when it dies again after a restart."""
    instance = Renderer([sys.executable, str(STAND_INS / "always_dies.py")], timeout=10)

    with pytest.raises(RendererError, match="render process exploded"):
        instance.draw({"index.d2": "a"}, 0, 200, "s")


def test_raise_when_node_does_not_answer(tmp_path: Path) -> None:
    """Raise once the time limit passes, without starting the process again."""
    starts = tmp_path / "starts"
    command = [sys.executable, str(STAND_INS / "never_answers.py"), str(starts)]
    instance = Renderer(command, timeout=0.5)

    with pytest.raises(RendererError, match="no answer within 0.5 s"):
        instance.draw({"index.d2": "a"}, 0, 200, "s")
    instance.close()

    assert starts.read_text(encoding="utf-8").splitlines() == ["started"]


def test_skip_lines_that_are_not_the_reply() -> None:
    """Ignore a log line and a reply to another request."""
    instance = Renderer([sys.executable, str(STAND_INS / "chatty.py")], timeout=10)

    assert instance.draw({"index.d2": "a"}, 0, 200, "s")[0].name == ""
    assert instance.draw({"index.d2": "b"}, 0, 200, "s")[0].name == ""
    instance.close()


def test_render_an_import_with_an_embedded_icon(
    renderer: Renderer, tmp_path: Path
) -> None:
    """Render quoted and nested imports, and an icon inside an imported file."""
    (tmp_path / "my parts").mkdir()
    (tmp_path / "my parts" / "stage.d2").write_text(
        "motor: { icon: cam.svg }\nhome: @home\n", encoding="utf-8"
    )
    (tmp_path / "my parts" / "home.d2").write_text("origin_shape\n", encoding="utf-8")
    (tmp_path / "cam.svg").write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')

    files = prepare('stage: @"my parts/stage"\n', tmp_path)
    svg = renderer.draw(files, 0, 200, "s")[0].light

    assert "motor" in svg and "origin_shape" in svg
    assert "data:image/svg+xml;base64," in svg


def test_report_a_repeated_d2_error_once(renderer: Renderer) -> None:
    """Drop a message D2 reports twice for the same place."""
    source = "vars: { d2-config: { animate-interval: 1000 } }\na\nsteps: { 1: { b } }\n"

    with pytest.raises(D2Error) as caught:
        renderer.draw({"index.d2": source}, 0, 200, "s")

    assert caught.value.messages == [
        'index.d2:1:22: "animate-interval" is not a valid config'
    ]


def test_apply_each_themes_own_overrides(renderer: Renderer) -> None:
    """Give the light picture the theme overrides and the dark one the dark ones."""
    source = (
        "vars: {\n  d2-config: {\n"
        '    theme-overrides: { B1: "#C62828" }\n'
        '    dark-theme-overrides: { B1: "#EF5350" }\n'
        "  }\n}\na -> b\n"
    )
    board = renderer.draw({"index.d2": source}, 0, 200, "s")[0]

    assert "#C62828" in board.light and "#EF5350" not in board.light
    assert "#EF5350" in board.dark and "#C62828" not in board.dark
