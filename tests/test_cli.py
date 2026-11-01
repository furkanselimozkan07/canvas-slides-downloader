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
    assert args.formats == ["pdf", "pptx"]
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


def test_input_file_merges_with_cli_urls(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr("slides_downloader.cli.sync_playwright", _FakePlaywright)
    monkeypatch.setattr("slides_downloader.cli.download", lambda pw, url, args: seen.append(url))
    listing = tmp_path / "urls.txt"
    listing.write_text("# term\nhttps://a.edu/2\nhttps://a.edu/1  # dup\n", encoding="utf-8")

    assert main(["https://a.edu/1", "-i", str(listing)]) == 0
    assert seen == ["https://a.edu/1", "https://a.edu/2"]


def test_no_urls_is_an_error():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_missing_input_file_is_an_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["-i", str(tmp_path / "nope.txt")])
    assert exc.value.code == 2


def test_skip_existing_avoids_capture(tmp_path, monkeypatch):
    from slides_downloader import cli

    (tmp_path / "lec").mkdir()
    (tmp_path / "lec" / "lec.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr(cli, "capture_deck", lambda *a, **k: pytest.fail("should not capture"))
    args = build_parser().parse_args(
        ["https://docs.google.com/presentation/d/e/ABC/pub", "-n", "lec", "-f", "pdf",
         "-o", str(tmp_path), "--skip-existing"]
    )
    cli.download(None, args.urls[0], args)


class _FakePlaywright:
    def __enter__(self):
        return object()

    def __exit__(self, *exc):
        return False
