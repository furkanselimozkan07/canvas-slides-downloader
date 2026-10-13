import argparse

import pytest

from slides_downloader.browser import channel_candidates
from slides_downloader.cli import build_parser, main, parse_formats


def test_parse_formats_normalizes_and_deduplicates():
    assert parse_formats(" PDF, png,pdf ") == ["pdf", "png"]


@pytest.mark.parametrize("value", ["", "docx", "pdf,gif"])
def test_parse_formats_rejects_invalid(value):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_formats(value)


def test_parser_defaults():
    args = build_parser().parse_args(["https://example.edu/page"])
    assert args.formats == ["pdf", "pptx", "png"]
    assert args.browser == "auto"
    assert args.name is None


def test_name_requires_single_url():
    with pytest.raises(SystemExit) as exc:
        main(["-n", "x", "https://a.edu/1", "https://a.edu/2"])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    ("browser", "expected"),
    [
        ("auto", (None, "chrome", "msedge")),
        ("chromium", (None,)),
        ("msedge", ("msedge",)),
    ],
)
def test_channel_candidates(browser, expected):
    assert channel_candidates(browser) == expected
