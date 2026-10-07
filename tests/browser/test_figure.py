"""The figure in a real browser: steps, full screen, themes."""

from __future__ import annotations

from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright

pytestmark = pytest.mark.browser

STEPS = (
    '```d2 title="Three steps"\nstart\nsteps: {\n  1: { middle }\n  2: { end }\n}\n```'
)
SCREENSHOTS = Path("test-results")


@pytest.fixture
def browser() -> Generator[Browser, None, None]:
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def opened(page: Callable[..., str], browser: Browser, tmp_path: Path) -> Page:
    html = page(STEPS)
    file = tmp_path / "index.html"
    file.write_text(f"<!doctype html><body>{html}</body>", encoding="utf-8")
    tab = browser.new_page()
    tab.goto(file.as_uri())
    return tab


def test_step_open_full_screen_and_switch_theme(opened: Page) -> None:
    """Step with buttons and keys, zoom in full screen, and follow the theme."""
    figure = opened.locator("figure.markdown-d2")
    counter = figure.locator(".markdown-d2-counter")
    expect(counter).to_have_text("1 / 3")

    figure.get_by_role("button", name="Next step").click()
    expect(counter).to_have_text("2 / 3 · steps.1")
    figure.focus()
    opened.keyboard.press("ArrowRight")
    expect(counter).to_have_text("3 / 3 · steps.2")
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
    SCREENSHOTS.mkdir(exist_ok=True)
    opened.screenshot(path=SCREENSHOTS / "full-screen.png")
    opened.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()

    expect(figure.locator(".markdown-d2-current .markdown-d2-light")).to_be_visible()
    opened.evaluate("document.body.setAttribute('data-md-color-scheme', 'slate')")
    expect(figure.locator(".markdown-d2-current .markdown-d2-dark")).to_be_visible()
    expect(figure.locator(".markdown-d2-current .markdown-d2-light")).to_be_hidden()
    opened.screenshot(path=SCREENSHOTS / "dark.png")
