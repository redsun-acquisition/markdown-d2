"""The figure in a real browser: steps, full screen, themes."""

from __future__ import annotations

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import Browser, Locator, Page, expect, sync_playwright

pytestmark = pytest.mark.browser

STEPS = (
    '```d2 title="Three steps"\nstart\nsteps: {\n  1: { middle }\n  2: { end }\n}\n```'
)
SCREENSHOTS = Path("test-results")
LABELLED = (
    '```d2\nlabel: "The start."\na\n'
    'steps: {\n  1: { label: "One more box."; b }\n}\n```'
)
HOVER = (
    "```d2\nviews -> presenters\npresenters: { tooltip: Decides what happens and when. }\n"
    "presenters -> devices\n```"
)
ANIMATIONS = """() => document.getAnimations().map((animation) => {
  const keyframes = animation.effect.getKeyframes();
  return keyframes.some((frame) => frame.transform) ? "move" : "fade";
})"""


def above(upper: Locator, lower: Locator) -> bool:
    """Return whether *upper* ends before *lower* starts, from top to bottom."""
    top, bottom = upper.bounding_box(), lower.bounding_box()
    assert top is not None and bottom is not None
    return top["y"] + top["height"] <= bottom["y"]


@pytest.fixture
def browser() -> Generator[Browser, None, None]:
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def open_page(
    page: Callable[..., str], browser: Browser, tmp_path: Path
) -> Callable[..., Page]:
    def open_steps(
        motion: Literal["reduce", "no-preference"] = "no-preference",
        text: str = STEPS,
        **settings: str,
    ) -> Page:
        html = page(text, **settings)
        file = tmp_path / "index.html"
        file.write_text(f"<!doctype html><body>{html}</body>", encoding="utf-8")
        tab = browser.new_page(reduced_motion=motion)
        tab.goto(file.as_uri())
        return tab

    return open_steps


@pytest.fixture
def opened(open_page: Callable[..., Page]) -> Page:
    return open_page()


def test_step_open_full_screen_and_switch_theme(opened: Page) -> None:
    """Step with buttons and keys, zoom and step in full screen, follow the theme."""
    figure = opened.locator("figure.markdown-d2")
    counter = figure.locator(".markdown-d2-counter")
    expect(counter).to_have_text("1 / 3")

    figure.get_by_role("button", name="Next step").click()
    expect(counter).to_have_text("2 / 3 (steps.1)")
    figure.focus()
    opened.keyboard.press("ArrowRight")
    expect(counter).to_have_text("3 / 3 (steps.2)")
    expect(figure.locator(".markdown-d2-board.markdown-d2-current")).to_have_attribute(
        "data-name", "steps.2"
    )

    figure.get_by_role("button", name="Open full screen").click()
    dialog = opened.locator("dialog.markdown-d2-dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Zoom in").click()
    expect(dialog.locator(".markdown-d2-view")).to_have_attribute(
        "style", "transform: translate(0px, 0px) scale(1.25);"
    )
    dialog.get_by_role("button", name="Previous step").click()
    expect(dialog.locator(".markdown-d2-counter")).to_have_text("2 / 3 (steps.1)")
    expect(dialog.locator(".markdown-d2-view")).to_contain_text("middle")
    SCREENSHOTS.mkdir(exist_ok=True)
    opened.screenshot(path=SCREENSHOTS / "full-screen.png")
    opened.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    expect(counter).to_have_text("2 / 3 (steps.1)")

    expect(figure.locator(".markdown-d2-current .markdown-d2-light")).to_be_visible()
    opened.evaluate("document.body.setAttribute('data-md-color-scheme', 'slate')")
    expect(figure.locator(".markdown-d2-current .markdown-d2-dark")).to_be_visible()
    expect(figure.locator(".markdown-d2-current .markdown-d2-light")).to_be_hidden()
    opened.screenshot(path=SCREENSHOTS / "dark.png")


@pytest.mark.parametrize(
    ("transition", "motion", "kinds"),
    [
        ("none", "no-preference", set()),
        ("fade", "no-preference", {"fade"}),
        ("morph", "no-preference", {"move", "fade"}),
        ("morph", "reduce", set()),
    ],
)
def test_animate_the_change_of_step(
    open_page: Callable[..., Page], transition: str, motion: str, kinds: set[str]
) -> None:
    """Fade or move shapes to the next step, and keep still when asked to."""
    tab = open_page(motion, transition=transition)
    figure = tab.locator("figure.markdown-d2")
    expect(figure.locator(".markdown-d2-counter")).to_have_text("1 / 3")

    figure.get_by_role("button", name="Next step").click()

    assert set(tab.evaluate(ANIMATIONS)) == kinds


def test_highlight_a_shape_and_show_its_tooltip(open_page: Callable[..., Page]) -> None:
    """Fade the other shapes and show the tooltip of the shape under the pointer."""
    tab = open_page(text=HOVER)
    shapes = tab.locator(
        ".markdown-d2-current .markdown-d2-light svg.d2-svg > g:not(.appendix-icon)"
    )

    tab.locator(
        ".markdown-d2-current .markdown-d2-light svg text", has_text="presenters"
    ).hover()

    tooltip = tab.locator(".markdown-d2-tooltip")
    expect(tooltip).to_be_visible()
    expect(tooltip).to_have_text("Decides what happens and when.")
    expect(tab.locator(".markdown-d2-current .markdown-d2-light title")).to_have_count(
        0
    )
    opacities = [
        float(shapes.nth(i).evaluate("g => getComputedStyle(g).opacity"))
        for i in range(shapes.count())
    ]
    assert max(opacities) == 1.0 and opacities.count(1.0) == 1

    tab.mouse.move(0, 0)
    expect(tooltip).to_be_hidden()


def test_put_the_step_buttons_above_the_diagram(opened: Page) -> None:
    """Show the step buttons above the picture, in the figure and in full screen."""
    figure = opened.locator("figure.markdown-d2")
    controls = figure.locator(".markdown-d2-controls")
    board = figure.locator(".markdown-d2-current")

    assert above(controls, board)

    figure.get_by_role("button", name="Open full screen").click()
    dialog = opened.locator("dialog.markdown-d2-dialog")
    assert above(
        dialog.locator(".markdown-d2-controls"), dialog.locator(".markdown-d2-stage")
    )


def test_change_the_text_with_the_step(open_page: Callable[..., Page]) -> None:
    """Show only the current board's text, between the buttons and the picture."""
    tab = open_page(text=LABELLED)
    figure = tab.locator("figure.markdown-d2")
    text = figure.locator(".markdown-d2-text")

    expect(text.filter(visible=True)).to_have_text("The start.")
    assert above(figure.locator(".markdown-d2-controls"), text.filter(visible=True))
    assert above(
        text.filter(visible=True),
        figure.locator(".markdown-d2-current .markdown-d2-light"),
    )
    figure.get_by_role("button", name="Next step").click()
    expect(text.filter(visible=True)).to_have_text("One more box.")
