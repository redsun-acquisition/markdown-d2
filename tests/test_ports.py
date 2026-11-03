"""Shapes marked as ports, moved onto the edge of their block."""

from __future__ import annotations

import base64
import re
from collections.abc import Generator

import pytest

from markdown_d2._paths import default_node
from markdown_d2._renderer import D2Error, Renderer, node_command

DOT = "classes: {dot: {shape: circle; width: 16; height: 16}}\n"
PAIR = (
    DOT
    + "direction: right\n"
    + "a: { o: {class: [dot; port-right]}; spare: {class: [dot; port-left]} }\n"
    + "b: { i: {class: [dot; port-left]} }\n"
    + "a.o -- b.i\n"
    + "steps: { 1: { c } }\n"
)
ATTRIBUTE = re.compile(r'([\w-]+)="([^"]*)"')


@pytest.fixture
def renderer() -> Generator[Renderer, None, None]:
    instance = Renderer(node_command(default_node()), timeout=60)
    yield instance
    instance.close()


def group(svg: str, name: str) -> str:
    """Return the text of the SVG group D2 drew for the shape or link *name*."""
    # D2 escapes the quotes of a quoted name before it encodes the name
    tag = base64.b64encode(name.replace('"', "&#34;").encode()).decode()
    start = re.search(rf'<g class="{re.escape(tag)}[" ]', svg)
    assert start is not None, f"no group for {name}"
    return svg[start.start() :]


def box(svg: str, name: str) -> tuple[float, float, float, float]:
    """Return the x, y, width and height of the shape *name*."""
    found = re.search(r"<(rect|ellipse) ([^>]*)>", group(svg, name))
    assert found is not None
    values = {key: float(value) for key, value in ATTRIBUTE.findall(found[2])
              if key in {"x", "y", "width", "height", "cx", "cy", "rx", "ry"}}
    if found[1] == "ellipse":
        return (
            values["cx"] - values["rx"],
            values["cy"] - values["ry"],
            2 * values["rx"],
            2 * values["ry"],
        )
    return values["x"], values["y"], values["width"], values["height"]


def centre(svg: str, name: str) -> tuple[float, float]:
    """Return the centre of the shape *name*."""
    x, y, width, height = box(svg, name)
    return x + width / 2, y + height / 2


def edges(svg: str, name: str) -> tuple[float, float]:
    """Return the left and right edge of the shape *name*."""
    x, _, width, _ = box(svg, name)
    return x, x + width


def ends(svg: str, link: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the first and last point of the path drawn for *link*."""
    found = re.search(r'<path d="([^"]*)"', group(svg, link))
    assert found is not None
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", found[1])]
    return (numbers[0], numbers[1]), (numbers[-2], numbers[-1])


def draw(renderer: Renderer, source: str) -> dict[str, str]:
    """Return the light SVG of each board of *source*, by board name."""
    boards = renderer.draw({"index.d2": source}, 0, 200, "s")
    return {board.name: board.light for board in boards}


def test_put_each_port_on_its_blocks_edge(renderer: Renderer) -> None:
    """Centre each port on its block's edge, level with the port it links to."""
    for svg in draw(renderer, PAIR).values():
        assert centre(svg, "a.o")[0] == pytest.approx(edges(svg, "a")[1], abs=0.5)
        assert centre(svg, "b.i")[0] == pytest.approx(edges(svg, "b")[0], abs=0.5)
        assert centre(svg, "a.spare")[0] == pytest.approx(edges(svg, "a")[0], abs=0.5)
        assert centre(svg, "a.o")[1] == pytest.approx(centre(svg, "b.i")[1], abs=0.5)


def test_find_the_parent_of_a_quoted_name(renderer: Renderer) -> None:
    """Take the block whose quoted name has a dot as the port's parent."""
    svg = draw(renderer, DOT + '"v1.2": { p: {class: [dot; port-left]} }\n')[""]

    assert centre(svg, '"v1.2".p')[0] == pytest.approx(edges(svg, '"v1.2"')[0], abs=0.5)


def test_use_the_inner_block_of_nested_blocks(renderer: Renderer) -> None:
    """Move a port onto the edge of the innermost block holding it."""
    svg = draw(renderer, DOT + "outer: { inner: { p: {class: [dot; port-right]} } }\n")[""]

    assert centre(svg, "outer.inner.p")[0] == pytest.approx(
        edges(svg, "outer.inner")[1], abs=0.5
    )


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            DOT + "m: { p: {class: [dot; port-top]} }\n",
            "port-top and port-bottom are not supported yet",
        ),
        (
            "vars: {d2-config: {layout-engine: elk}}\n"
            + DOT
            + "m: { p: {class: [dot; port-left]} }\n",
            "ports need the dagre layout",
        ),
        (DOT + "p: {class: [dot; port-left]}\n", "a port needs a parent block"),
        (
            DOT
            + "m: { shape: sequence_diagram; p: {class: [dot; port-left]}; q; p -> q }\n",
            "ports cannot sit on a sequence diagram",
        ),
    ],
)
def test_refuse_what_ports_do_not_support(
    renderer: Renderer, source: str, message: str
) -> None:
    """Refuse top and bottom ports, elk, a port alone and one in a sequence diagram."""
    with pytest.raises(D2Error, match=r'port "[^"]+": ' + re.escape(message)):
        renderer.draw({"index.d2": source}, 0, 200, "s")
