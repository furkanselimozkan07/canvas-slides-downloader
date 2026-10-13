"""Finding Google Slides decks embedded in an LMS page (Canvas, Moodle, ...).

LMS pages need a signed-in session, so a visible browser window is opened with
a persistent profile. The user signs in once; later runs reuse the session.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, Playwright

from slides_downloader.browser import launch_persistent_context
from slides_downloader.errors import AccessDeniedError, DeckNotFoundError

log = logging.getLogger(__name__)

IFRAME_SELECTOR = 'iframe[src*="docs.google.com/presentation"]'
# Canvas renders its "Unauthorized" page under the requested URL itself.
_DENIED_SELECTORS = ("#unauthorized_message",)
_DENIED_TITLES = ("unauthorized", "access denied", "not authorized", "page not found")
POLL_INTERVAL = 1.0


def _same_page(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return pa.netloc == pb.netloc and pa.path.rstrip("/") == pb.path.rstrip("/")


def _is_after_login_redirect(current: str, target: str) -> bool:
    """True when the LMS sent us to its dashboard (same host, other page) after login."""
    cur, tgt = urlparse(current), urlparse(target)
    return cur.netloc == tgt.netloc and "login" not in cur.path.lower() and not _same_page(current, target)


def _is_access_denied(page: Page) -> bool:
    if any(page.query_selector(sel) for sel in _DENIED_SELECTORS):
        return True
    title = page.title().lower()
    return any(marker in title for marker in _DENIED_TITLES)


def _embedded_decks(page: Page) -> list[str]:
    sources = (frame.get_attribute("src") for frame in page.query_selector_all(IFRAME_SELECTOR))
    return list(dict.fromkeys(src for src in sources if src))  # de-duplicate, keep order


def find_embedded_decks(
    playwright: Playwright,
    page_url: str,
    *,
    profile_dir: Path,
    browser: str,
    login_timeout: float,
) -> list[str]:
    """Open ``page_url`` and return the ``src`` of every embedded Google Slides deck."""
    context = launch_persistent_context(
        playwright, profile_dir, browser, headless=False, viewport={"width": 1280, "height": 900}
    )
    try:
        page = context.pages[0] if context.pages else context.new_page()
        log.info("Opening %s", page_url)
        log.info("If you are asked to sign in, do it in the browser window (%.0f s timeout).", login_timeout)
        page.goto(page_url)

        deadline = time.monotonic() + login_timeout
        returned_to_target = False
        while time.monotonic() < deadline:
            try:
                if not returned_to_target and _is_after_login_redirect(page.url, page_url):
                    returned_to_target = True
                    page.goto(page_url)
                    continue
                decks = _embedded_decks(page)
                if decks:
                    return decks
                if _same_page(page.url, page_url) and _is_access_denied(page):
                    raise AccessDeniedError(
                        f"Your account is not allowed to view {page_url} "
                        "(are you enrolled in this course?)."
                    )
            except PlaywrightError:
                pass  # page is navigating; try again on the next tick
            time.sleep(POLL_INTERVAL)
    finally:
        context.close()

    raise DeckNotFoundError(
        f"No embedded Google Slides deck found on {page_url} "
        "(not signed in in time, or the page has no Google Slides)."
    )
