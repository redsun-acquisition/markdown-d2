"""The Node process that renders diagrams."""

from __future__ import annotations

import sys
import threading
from collections.abc import Generator
from pathlib import Path

import pytest

from markdown_d2._paths import default_node
from markdown_d2._renderer import D2Error, Renderer, RendererError, node_command
from markdown_d2._sources import prepare

STAND_INS = Path(__file__).parent / "stand_ins"
STEPS = "alpha_top\nsteps: {\n  1: { beta_first }\n  2: { gamma_second }\n}\n"


@pytest.fixture
def renderer() -> Generator[Renderer, None, None]:
    instance = Renderer(node_command(default_node()), timeout=60)
    yield instance
    instance.close()


def test_list_and_render_boards(renderer: Renderer) -> None:
    """List a diagram's boards and render the top board and a step."""
    files = {"index.d2": STEPS}

    boards = renderer.boards(files)
    top = renderer.render(files, "", "light", 0, 200, "s1")
    second = renderer.render(files, "steps.2", "dark", 0, 200, "s2")

    assert boards == ["", "steps.1", "steps.2"]
    assert "alpha_top" in top and "beta_first" not in top
    assert "gamma_second" in second
    assert "#1E1E2E" in second
    assert "prefers-color-scheme" not in second


def test_keep_text_that_is_not_ascii(renderer: Renderer) -> None:
    """Carry a label with non-ASCII text through the pipe unchanged."""
    source = "s: stage (µm)\na: Ångström\ns -> a\n"
    svg = renderer.render({"index.d2": source}, "", "light", 0, 200, "s")

    assert "stage (µm)" in svg
    assert "Ångström" in svg


def test_answer_two_threads_with_their_own_svgs(renderer: Renderer) -> None:
    """Give each of two concurrent callers the SVG of its own diagram."""
    results: dict[str, str] = {}

    def work(label: str) -> None:
        results[label] = renderer.render(
            {"index.d2": label}, "", "light", 0, 200, label
        )

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
        renderer.boards({"index.d2": "a -> \n b: {"})

    assert caught.value.messages == [
        "index.d2:1:1: connection missing destination",
        "index.d2:2:5: maps must be terminated with }",
    ]


def test_restart_node_once_after_a_crash(tmp_path: Path) -> None:
    """Restart a process that died, and answer from the new one."""
    command = [sys.executable, str(STAND_INS / "dies_once.py"), str(tmp_path / "flag")]
    instance = Renderer(command, timeout=10)

    assert instance.boards({"index.d2": "a"}) == [""]
    instance.close()


def test_raise_when_node_dies_twice() -> None:
    """Raise with the process's own output when it dies again after a restart."""
    instance = Renderer([sys.executable, str(STAND_INS / "always_dies.py")], timeout=10)

    with pytest.raises(RendererError, match="render process exploded"):
        instance.boards({"index.d2": "a"})


def test_raise_when_node_does_not_answer() -> None:
    """Raise once the time limit passes without an answer."""
    instance = Renderer(
        [sys.executable, str(STAND_INS / "never_answers.py")], timeout=0.5
    )

    with pytest.raises(RendererError, match="no answer within 0.5 s"):
        instance.boards({"index.d2": "a"})
    instance.close()


def test_render_an_import_with_an_embedded_icon(
    renderer: Renderer, tmp_path: Path
) -> None:
    """Render an imported file that carries an icon and imports its neighbour."""
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "stage.d2").write_text(
        "motor: { icon: cam.svg }\nhome: @home\n", encoding="utf-8"
    )
    (tmp_path / "parts" / "home.d2").write_text("origin_shape\n", encoding="utf-8")
    (tmp_path / "cam.svg").write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')

    svg = renderer.render(
        prepare("stage: @parts/stage\n", tmp_path), "", "light", 0, 200, "s"
    )

    assert "motor" in svg and "origin_shape" in svg
    assert "data:image/svg+xml;base64," in svg
