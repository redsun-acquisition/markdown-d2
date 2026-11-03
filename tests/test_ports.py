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
ESCAPES = str.maketrans(
    {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&#34;", "'": "&#39;"}
)
DOT_BORDER = 9
FAN = (
    DOT
    + "direction: right\n"
    + "a: { o: {class: [dot; port-right]} }\n"
    + "b: { i: {class: [dot; port-left]}; j: {class: [dot; port-left]} }\n"
    + "a.o -- b.i\n"
    + "a.o -- b.j\n"
    + "steps: { 1: { c } }\n"
)
BOTH_WAYS = "p.o -> v.i\nv.o -> p.i\n"
FEEDBACK = (
    DOT
    + "direction: right\n"
    + "p: { i: {class: [dot; port-left]}; o: {class: [dot; port-right]} }\n"
    + "v: { i: {class: [dot; port-left]}; o: {class: [dot; port-right]} }\n"
    + "p.o -- v.i\n"
    + "p.i -- v.o\n"
)


@pytest.fixture
def renderer() -> Generator[Renderer, None, None]:
    instance = Renderer(node_command(default_node()), timeout=60)
    yield instance
    instance.close()


def group(svg: str, name: str) -> str:
    """Return the text of the SVG group D2 drew for the shape or link *name*."""
    # D2 escapes the name for HTML, the way Go does, before it encodes it
    tag = base64.b64encode(name.translate(ESCAPES).encode()).decode()
    start = re.search(rf'<g class="{re.escape(tag)}[" ]', svg)
    assert start is not None, f"no group for {name}"
    return svg[start.start() :]


def box(svg: str, name: str) -> tuple[float, float, float, float]:
    """Return the x, y, width and height of the shape *name*."""
    found = re.search(r"<(rect|ellipse) ([^>]*)>", group(svg, name))
    assert found is not None
    values = {
        key: float(value)
        for key, value in ATTRIBUTE.findall(found[2])
        if key in {"x", "y", "width", "height", "cx", "cy", "rx", "ry"}
    }
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


def points(svg: str, link: str) -> list[tuple[float, float]]:
    """Return the points of the path drawn for *link*, control points included."""
    found = re.search(r'<path d="([^"]*)"', group(svg, link))
    assert found is not None
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", found[1])]
    return list(zip(numbers[::2], numbers[1::2], strict=True))


def ends(svg: str, link: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the first and last point of the path drawn for *link*."""
    route = points(svg, link)
    return route[0], route[-1]


def inside(svg: str, link: str, name: str) -> list[tuple[float, float]]:
    """Return the points along the path of *link* that lie inside the shape *name*."""
    route = points(svg, link)
    x, y, width, height = box(svg, name)
    found = []
    for start in range(0, len(route) - 3, 3):
        a, b, c, d = route[start : start + 4]
        for step in range(1, 40):
            t = step / 40
            px, py = (
                (1 - t) ** 3 * a[i]
                + 3 * (1 - t) ** 2 * t * b[i]
                + 3 * (1 - t) * t**2 * c[i]
                + t**3 * d[i]
                for i in (0, 1)
            )
            # the 2 px margin lets a link end on a marker that sits on the edge
            if x + 2 < px < x + width - 2 and y + 2 < py < y + height - 2:
                found.append((px, py))
    return found


def assert_on_border(
    svg: str,
    point: tuple[float, float],
    port: str,
    side: int,
    border: float,
    slack: float = 3,
) -> None:
    """Check that *point* lies on the *side* of the marker drawn for *port*."""
    x, y = centre(svg, port)
    # D2 trims a few px off each end of a drawn path, more under an arrowhead
    assert point[0] == pytest.approx(x + side * border, abs=slack)
    assert point[1] == pytest.approx(y, abs=3)


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
    svg = draw(renderer, DOT + "outer: { inner: { p: {class: [dot; port-right]} } }\n")[
        ""
    ]

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
        (
            "vars: {d2-config: {layout-engine: elk}}\n"
            + DOT
            + "layers: { l: { m: { p: {class: [dot; port-left]} } } }\n",
            "ports need the dagre layout",
        ),
        (
            DOT
            + "g: { grid-columns: 2; p: {class: [dot; port-left]}; q }\ng.p -> g.q\n",
            "a port cannot have a link that runs straight",
        ),
    ],
)
def test_refuse_what_ports_do_not_support(
    renderer: Renderer, source: str, message: str
) -> None:
    """Refuse top and bottom ports, elk, a port alone and one in a sequence diagram."""
    with pytest.raises(D2Error, match=r'port "[^"]+": ' + re.escape(message)):
        renderer.draw({"index.d2": source}, 0, 200, "s")


def test_meet_each_port_at_its_border(renderer: Renderer) -> None:
    """Start and end every link, a fan-out included, on its markers' borders."""
    for svg in draw(renderer, FAN).values():
        for target in ("b.i", "b.j"):
            start, end = ends(svg, f"(a.o -- {target})[0]")
            assert_on_border(svg, start, "a.o", 1, DOT_BORDER)
            assert_on_border(svg, end, target, -1, DOT_BORDER)


@pytest.mark.parametrize("v_side", [-1, 1])
def test_join_links_that_run_back(renderer: Renderer, v_side: int) -> None:
    """Keep each link out of its ports' blocks when two blocks link both ways."""
    v_class = "port-left" if v_side < 0 else "port-right"
    links = ("p.o -- v.i", "p.i -- v.o")
    source = (
        DOT
        + "direction: right\n"
        + "p: { o: {class: [dot; port-right]}; i: {class: [dot; port-right]} }\n"
        + f"v: {{ i: {{class: [dot; {v_class}]}}; o: {{class: [dot; {v_class}]}} }}\n"
        + "".join(f"{link}\n" for link in links)
    )
    svg = draw(renderer, source)[""]
    sides = {"p": 1, "v": v_side}

    for link in links:
        src, dst = link.split(" -- ")
        start, end = ends(svg, f"({link})[0]")
        for port, point in ((src, start), (dst, end)):
            block = port.split(".")[0]
            assert_on_border(svg, point, port, sides[block], DOT_BORDER)
            assert inside(svg, f"({link})[0]", block) == []


def test_join_inward_to_a_shape_in_the_same_block(renderer: Renderer) -> None:
    """Leave a port toward the inside when its link runs to a shape in its block."""
    source = DOT + "b: { i: {class: [dot; port-left]}; core }\nb.i -> b.core\n"
    svg = draw(renderer, source)[""]
    route = points(svg, "b.(i -> core)[0]")
    x, y, width, height = box(svg, "b")

    assert_on_border(svg, route[0], "b.i", 1, DOT_BORDER)
    for px, py in route:
        assert x <= px <= x + width
        assert y <= py <= y + height


def test_join_two_ports_of_one_block(renderer: Renderer) -> None:
    """Join a block's left port to its right port from their inner borders."""
    source = (
        DOT
        + "b: { i: {class: [dot; port-left]}; o: {class: [dot; port-right]} }\n"
        + "b.i -- b.o\n"
    )
    svg = draw(renderer, source)[""]
    start, end = ends(svg, "b.(i -- o)[0]")

    assert_on_border(svg, start, "b.i", 1, DOT_BORDER)
    assert_on_border(svg, end, "b.o", -1, DOT_BORDER)


def test_meet_a_marker_filled_through_its_stroke(renderer: Renderer) -> None:
    """Meet a marker filled by a thick stroke at the border a reader sees."""
    source = (
        "classes: {fat: {shape: square; width: 8; height: 8; "
        "style: {fill: transparent; stroke-width: 8}}}\n"
        "direction: right\n"
        "a: { o: {class: [fat; port-right]} }\n"
        "b: { i: {class: [fat; port-left]} }\n"
        "a.o -- b.i\n"
    )
    svg = draw(renderer, source)[""]
    start, end = ends(svg, "(a.o -- b.i)[0]")

    assert_on_border(svg, start, "a.o", 1, 8)
    assert_on_border(svg, end, "b.i", -1, 8)


def test_refuse_ports_that_overlap(renderer: Renderer) -> None:
    """Refuse two ports that land on one spot, as they do without direction: right."""
    source = (
        DOT + "a: { o: {class: [dot; port-right]}; p: {class: [dot; port-right]} }\n"
    )

    with pytest.raises(D2Error, match=r"overlaps port .*use direction: right"):
        renderer.draw({"index.d2": source}, 0, 200, "s")


def test_name_dashes_when_arrows_stack_the_containers(renderer: Renderer) -> None:
    """Tell the author to write -- when arrows both ways stack two containers."""
    source = (
        DOT
        + "direction: right\n"
        + "p: { o: {class: [dot; port-right]}; i: {class: [dot; port-right]} }\n"
        + "v: { i: {class: [dot; port-left]}; o: {class: [dot; port-left]} }\n"
        + BOTH_WAYS
    )

    with pytest.raises(D2Error, match="write the links between containers with --"):
        renderer.draw({"index.d2": source}, 0, 200, "s")


def test_refuse_a_name_that_crosses_the_far_edge(renderer: Renderer) -> None:
    """Refuse a port whose name reaches past the other edge of its block."""
    name = "a name that runs on for forty characters"
    source = (
        DOT
        + "m: {\n  grid-columns: 1\n  width: 60\n"
        + f'  p: "{name}" {{class: [dot; port-left]; label.near: outside-right-center}}\n'
        + "}\n"
    )

    with pytest.raises(D2Error, match="shorten the name"):
        renderer.draw({"index.d2": source}, 0, 200, "s")


def test_fit_a_long_name(renderer: Renderer) -> None:
    """Draw a block whose ports carry long names, with each port on its edge."""
    source = (
        DOT
        + "direction: right\nm: {\n"
        + '  devices: "devices: DeviceMapping" '
        + "{class: [dot; port-left]; label.near: outside-right-center}\n"
        + '  state: "state: Status" '
        + "{class: [dot; port-right]; label.near: outside-left-center}\n"
        + "}\n"
    )
    svg = draw(renderer, source)[""]

    assert centre(svg, "m.devices")[0] == pytest.approx(edges(svg, "m")[0], abs=0.5)
    assert centre(svg, "m.state")[0] == pytest.approx(edges(svg, "m")[1], abs=0.5)


def test_keep_a_port_highlighted_in_a_scenario(renderer: Renderer) -> None:
    """Keep a port on its edge on a scenario that replaces its classes."""
    source = (
        DOT
        + "classes.current: {style.stroke-width: 4}\n"
        + "m: { a: {class: [dot; port-left]}; b }\n"
        + "scenarios: { hl: { m.a.class: [current; dot; port-left] } }\n"
    )
    svg = draw(renderer, source)["scenarios.hl"]

    assert centre(svg, "m.a")[0] == pytest.approx(edges(svg, "m")[0], abs=0.5)


def test_go_around_the_container_for_a_link_behind_its_port(renderer: Renderer) -> None:
    """Take a feedback link around both containers instead of through them."""
    svg = draw(renderer, FEEDBACK)[""]
    start, end = ends(svg, "(p.i -- v.o)[0]")

    assert_on_border(svg, start, "p.i", -1, DOT_BORDER)
    assert_on_border(svg, end, "v.o", 1, DOT_BORDER)
    for link in ("(p.i -- v.o)[0]", "(p.o -- v.i)[0]"):
        assert inside(svg, link, "p") == []
        assert inside(svg, link, "v") == []
    bottom = max(
        box(svg, "p")[1] + box(svg, "p")[3], box(svg, "v")[1] + box(svg, "v")[3]
    )
    gap = (edges(svg, "p")[1], edges(svg, "v")[0])
    assert all(
        y > bottom for x, y in points(svg, "(p.i -- v.o)[0]") if gap[0] < x < gap[1]
    )
