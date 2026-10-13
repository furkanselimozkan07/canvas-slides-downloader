"""Launching a Chromium-based browser, falling back to installed Chrome / Edge.

Playwright's own Chromium build is preferred, but its download is large and
sometimes blocked (corporate / campus networks). In ``auto`` mode we fall back
to a Google Chrome or Microsoft Edge that is already installed on the system.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from playwright.sync_api import Browser, BrowserContext, Playwright
from playwright.sync_api import Error as PlaywrightError

from slides_downloader.errors import BrowserNotFoundError

BROWSER_CHOICES = ("auto", "chromium", "chrome", "msedge")

T = TypeVar("T")


def channel_candidates(browser: str) -> tuple[str | None, ...]:
    """Map a ``--browser`` choice to the Playwright channels to try, in order.

    ``None`` stands for Playwright's bundled Chromium.
    """
    if browser == "auto":
        return (None, "chrome", "msedge")
    if browser == "chromium":
        return (None,)
    if browser in BROWSER_CHOICES:
        return (browser,)
    raise ValueError(f"unknown browser: {browser!r}")


def _launch_with_fallback(launch: Callable[..., T], browser: str, **kwargs) -> T:
    failures = []
    for channel in channel_candidates(browser):
        try:
            return launch(channel=channel, **kwargs)
        except PlaywrightError as exc:
            reason = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
            failures.append(f"  - {channel or 'chromium'}: {reason}")
    raise BrowserNotFoundError(
        "Could not start a browser. Either run `python -m playwright install chromium`, "
        "or install Google Chrome / Microsoft Edge and use --browser chrome / msedge.\n"
        + "\n".join(failures)
    )


def launch_browser(playwright: Playwright, browser: str, **kwargs) -> Browser:
    return _launch_with_fallback(playwright.chromium.launch, browser, **kwargs)


def launch_persistent_context(
    playwright: Playwright, user_data_dir: Path, browser: str, **kwargs
) -> BrowserContext:
    """Launch a browser whose cookies persist in ``user_data_dir`` (keeps LMS logins)."""
    user_data_dir.mkdir(parents=True, exist_ok=True)

    def launch(**kw) -> BrowserContext:
        return playwright.chromium.launch_persistent_context(str(user_data_dir), **kw)

    return _launch_with_fallback(launch, browser, **kwargs)
