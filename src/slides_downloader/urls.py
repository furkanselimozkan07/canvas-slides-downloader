"""Pure helpers for working with Google Slides and LMS page URLs."""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import parse_qs, urlparse, urlunparse

GOOGLE_DOCS_HOST = "docs.google.com"

# Trailing path segments that say nothing about the content and make poor folder names.
_GENERIC_SEGMENTS = {"embed", "pub", "pubembed", "edit", "preview", "present", "view"}
_MAX_NAME_LENGTH = 60


def is_google_slides_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == GOOGLE_DOCS_HOST and parsed.path.startswith("/presentation/")


def to_embed_url(url: str) -> str:
    """Return the ``/embed`` form of a Google Slides link.

    Published links (``/d/e/<id>/pub``, ``/pubembed``, ``/embed``) and regular
    share links (``/d/<id>/edit``) are both normalized. Query parameters of an
    existing embed link are kept; anything else is passed through unchanged.
    """
    parsed = urlparse(url)
    if not is_google_slides_url(url):
        return url
    published = re.match(r"^(/presentation/d/e/[^/]+)(?:/[^/]*)?$", parsed.path)
    shared = re.match(r"^(/presentation/d/(?!e/)[^/]+)(?:/.*)?$", parsed.path)
    match = published or shared
    if not match:
        return url
    path = match.group(1) + "/embed"
    query = parsed.query if parsed.path == path else ""
    return urlunparse(parsed._replace(path=path, query=query, fragment=""))


def slide_id(url: str) -> str | None:
    """Return the current slide id (``slide=id.p3``) from a viewer URL, if present.

    The id stays the same while stepping through a slide's animations, which is
    what lets us keep only the final, fully built state of each slide.
    """
    parsed = urlparse(url)
    for part in (parsed.query, parsed.fragment):
        values = parse_qs(part).get("slide")
        if values:
            return values[0]
    return None


def name_from_url(url: str, default: str = "slides") -> str:
    """Derive a filesystem-safe name from the most descriptive path segment of a URL."""
    segments = [s for s in urlparse(url).path.split("/") if s]
    for segment in reversed(segments):
        if segment.lower() not in _GENERIC_SEGMENTS:
            name = re.sub(r"[^\w-]+", "_", segment).strip("_")
            if name:
                return name[:_MAX_NAME_LENGTH]
    return default


def parse_url_list(lines: Iterable[str]) -> list[str]:
    """Extract URLs from the lines of a text file.

    Blank lines and ``#`` comments (whole-line or trailing, after whitespace) are
    ignored, and duplicates are dropped while keeping the original order.
    """
    urls: list[str] = []
    for line in lines:
        text = re.split(r"\s#", line.strip(), maxsplit=1)[0].strip()
        if text and not text.startswith("#") and text not in urls:
            urls.append(text)
    return urls
