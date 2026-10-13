"""Capturing a Google Slides embed, one screenshot per slide.

The viewer is stepped with the right arrow key. Animated slides take several
steps but keep the same slide id, so only their final (fully built) state is
kept. Capture stops once the image no longer changes.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from playwright.sync_api import Page, Playwright

from slides_downloader.browser import launch_browser
from slides_downloader.urls import slide_id

VIEWPORT = {"width": 1920, "height": 1080}
# Elements that contain only the slide (no toolbar), most specific first.
SLIDE_SELECTORS = (
    ".punch-viewer-svgpage-svgcontainer",
    ".punch-viewer-svgpage",
    ".punch-viewer-content",
)
_MIN_SLIDE_WIDTH = 300
_UNCHANGED_STEPS_AT_END = 2


@dataclass(frozen=True)
class CaptureOptions:
    browser: str = "auto"
    step_delay: float = 1.2
    max_steps: int = 600
    scale: float = 1.5


def _screenshot_slide(page: Page) -> bytes:
    page.mouse.move(1, 1)  # move the cursor away so the viewer hides its toolbar
    time.sleep(0.4)
    for selector in SLIDE_SELECTORS:
        element = page.query_selector(selector)
        if element and element.is_visible():
            box = element.bounding_box()
            if box and box["width"] > _MIN_SLIDE_WIDTH:
                return element.screenshot()
    return page.screenshot()


def drop_consecutive_duplicates(images: list[bytes]) -> list[bytes]:
    return [img for i, img in enumerate(images) if i == 0 or img != images[i - 1]]


def capture_deck(
    playwright: Playwright,
    embed_url: str,
    options: CaptureOptions,
    on_slide: Callable[[int], None] | None = None,
) -> list[bytes]:
    """Return one PNG (bytes) per slide of the deck at ``embed_url``."""
    browser = launch_browser(playwright, options.browser)
    try:
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=options.scale)
        page.goto(embed_url, wait_until="networkidle")
        time.sleep(2)
        page.mouse.click(VIEWPORT["width"] // 2, VIEWPORT["height"] // 2)  # focus the viewer
        page.keyboard.press("Home")  # the click may have advanced; start from slide 1
        time.sleep(options.step_delay)

        slides: dict[str, bytes] = {}  # slide id -> latest screenshot of that slide
        previous = None
        unchanged = 0
        for step in range(options.max_steps):
            png = _screenshot_slide(page)
            key = slide_id(page.url) or f"step-{step}"
            if key not in slides and on_slide:
                on_slide(len(slides) + 1)
            slides[key] = png
            if png == previous:
                unchanged += 1
                if unchanged >= _UNCHANGED_STEPS_AT_END:
                    break
            else:
                unchanged = 0
            previous = png
            page.keyboard.press("ArrowRight")
            time.sleep(options.step_delay)
    finally:
        browser.close()

    return drop_consecutive_duplicates(list(slides.values()))
