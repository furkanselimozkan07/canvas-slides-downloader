"""Command-line interface: ``slides-dl URL [URL ...]``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from playwright.sync_api import Playwright, sync_playwright

from slides_downloader import __version__
from slides_downloader.browser import BROWSER_CHOICES
from slides_downloader.capture import CaptureOptions, capture_deck
from slides_downloader.discover import find_embedded_decks
from slides_downloader.errors import CaptureError, SlidesDownloaderError
from slides_downloader.export import DEFAULT_FORMATS, FORMATS, export, outputs_exist
from slides_downloader.urls import is_google_slides_url, name_from_url, parse_url_list, to_embed_url

log = logging.getLogger("slides_downloader")

DEFAULT_PROFILE_DIR = Path.home() / ".slides-downloader" / "browser-profile"


def parse_formats(value: str) -> list[str]:
    formats = [f.strip().lower() for f in value.split(",") if f.strip()]
    unknown = sorted(set(formats) - set(FORMATS))
    if not formats or unknown:
        raise argparse.ArgumentTypeError(
            f"invalid format(s): {', '.join(unknown) or value!r}; choose from {', '.join(FORMATS)}"
        )
    return list(dict.fromkeys(formats))


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slides-dl",
        description=(
            "Download Google Slides decks embedded in LMS pages (Canvas, Moodle, ...) "
            "or published Google Slides links as PDF and PPTX (PNG images optional)."
        ),
    )
    parser.add_argument("urls", nargs="*", metavar="URL", help="LMS page URL or Google Slides link")
    parser.add_argument(
        "-i", "--input-file", type=Path, metavar="FILE",
        help="text file with one URL per line ('-' reads stdin); blank lines and # comments are ignored",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="do not capture a deck again if all requested output files already exist",
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path.cwd(),
        help="where to create the output folders (default: current directory)",
    )
    parser.add_argument(
        "-n", "--name",
        help="output folder / file name (single URL only; default: derived from the URL)",
    )
    parser.add_argument(
        "-f", "--formats", type=parse_formats, default=list(DEFAULT_FORMATS),
        help=f"comma-separated output formats: {','.join(FORMATS)} (default: {','.join(DEFAULT_FORMATS)})",
    )
    parser.add_argument(
        "-b", "--browser", choices=BROWSER_CHOICES, default="auto",
        help="browser to use; 'auto' tries Playwright's Chromium, then Chrome, then Edge",
    )
    parser.add_argument(
        "--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR,
        help="browser profile that stores your LMS login (default: %(default)s)",
    )
    parser.add_argument(
        "--login-timeout", type=_positive_float, default=300,
        help="seconds to wait for you to sign in (default: %(default)s)",
    )
    parser.add_argument(
        "--delay", type=_positive_float, default=1.2,
        help="seconds to wait after each slide step; raise for slow connections (default: %(default)s)",
    )
    parser.add_argument(
        "--scale", type=_positive_float, default=1.5,
        help="screenshot scale factor; higher means sharper images (default: %(default)s)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=600,
        help="safety limit on slide/animation steps per deck (default: %(default)s)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def download(playwright: Playwright, url: str, args: argparse.Namespace) -> None:
    if is_google_slides_url(url):
        decks = [url]
    else:
        decks = find_embedded_decks(
            playwright, url,
            profile_dir=args.profile_dir, browser=args.browser, login_timeout=args.login_timeout,
        )
        log.info("Found %d Google Slides deck(s).", len(decks))

    options = CaptureOptions(
        browser=args.browser, step_delay=args.delay, max_steps=args.max_steps, scale=args.scale
    )
    base_name = args.name or name_from_url(url)
    for index, deck in enumerate(decks, 1):
        name = base_name if len(decks) == 1 else f"{base_name}_{index}"
        out_dir = args.output_dir / name
        if args.skip_existing and outputs_exist(out_dir, name, args.formats):
            log.info("Skipping %s (already downloaded in %s)", name, out_dir.resolve())
            continue
        embed_url = to_embed_url(deck)
        log.info("Capturing %s", embed_url)
        images = capture_deck(playwright, embed_url, options, on_slide=lambda n: log.info("  slide %d", n))
        if not images:
            raise CaptureError(
                "No slides were captured. Make sure the deck is published to the web "
                "or shared with 'anyone with the link'."
            )
        paths = export(images, out_dir, name, args.formats)
        log.info("Done: %d slides", len(images))
        for path in paths:
            if path.suffix != ".png":
                log.info("  %s", path.resolve())
        if "png" in args.formats:
            log.info("  %s (PNG images)", out_dir.resolve())


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.input_file:
        try:
            lines = (
                sys.stdin.read().splitlines()
                if str(args.input_file) == "-"
                else args.input_file.read_text(encoding="utf-8-sig").splitlines()
            )
        except OSError as exc:
            parser.error(f"cannot read {args.input_file}: {exc.strerror or exc}")
        args.urls = list(dict.fromkeys([*args.urls, *parse_url_list(lines)]))
    if not args.urls:
        parser.error("provide at least one URL (or use --input-file)")
    if args.name and len(args.urls) > 1:
        parser.error("--name can only be used with a single URL")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    failed = []
    with sync_playwright() as playwright:
        for url in args.urls:
            try:
                download(playwright, url, args)
            except SlidesDownloaderError as exc:
                log.error("Error: %s", exc)
                failed.append(url)
            except KeyboardInterrupt:
                log.error("Interrupted.")
                return 130

    if failed and len(args.urls) > 1:
        log.error("\n%d of %d URL(s) failed:\n  %s", len(failed), len(args.urls), "\n  ".join(failed))
    return 1 if failed else 0
