"""Exception types. Every error the CLI reports to the user derives from SlidesDownloaderError."""


class SlidesDownloaderError(Exception):
    """Base class for expected, user-facing errors."""


class BrowserNotFoundError(SlidesDownloaderError):
    """No usable Chromium-based browser could be launched."""


class AccessDeniedError(SlidesDownloaderError):
    """The LMS page reports that the signed-in user may not view it."""


class DeckNotFoundError(SlidesDownloaderError):
    """No embedded Google Slides deck was found on the page in time."""


class CaptureError(SlidesDownloaderError):
    """The deck was found but no slides could be captured."""
