import io

import pytest
from PIL import Image
from pptx import Presentation

from slides_downloader.capture import drop_consecutive_duplicates
from slides_downloader.export import export


def _png(color: str, size=(160, 90)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def images():
    return [_png("red"), _png("green"), _png("blue")]


def test_export_all_formats(tmp_path, images):
    paths = export(images, tmp_path / "deck", "deck", ["pdf", "pptx", "png"])

    names = sorted(p.name for p in paths)
    assert names == ["deck.pdf", "deck.pptx", "slide_001.png", "slide_002.png", "slide_003.png"]
    assert all(p.stat().st_size > 0 for p in paths)

    prs = Presentation(str(tmp_path / "deck" / "deck.pptx"))
    assert len(prs.slides) == 3
    assert prs.slide_width * 90 == prs.slide_height * 160  # aspect ratio follows the images


def test_export_only_pdf(tmp_path, images):
    paths = export(images, tmp_path / "deck", "deck", ["pdf"])
    assert [p.name for p in paths] == ["deck.pdf"]
    assert not list((tmp_path / "deck").glob("*.png"))


def test_export_png_replaces_stale_files(tmp_path, images):
    out = tmp_path / "deck"
    export(images, out, "deck", ["png"])
    export(images[:1], out, "deck", ["png"])
    assert [p.name for p in out.glob("slide_*.png")] == ["slide_001.png"]


def test_export_rejects_empty(tmp_path):
    with pytest.raises(ValueError):
        export([], tmp_path, "deck", ["pdf"])


def test_drop_consecutive_duplicates():
    a, b = b"a", b"b"
    assert drop_consecutive_duplicates([a, a, b, b, a]) == [a, b, a]
    assert drop_consecutive_duplicates([]) == []


def test_outputs_exist(tmp_path, images):
    from slides_downloader.export import outputs_exist

    out = tmp_path / "deck"
    assert not outputs_exist(out, "deck", ["pdf"])
    export(images, out, "deck", ["pdf", "png"])
    assert outputs_exist(out, "deck", ["pdf"])
    assert outputs_exist(out, "deck", ["pdf", "png"])
    assert not outputs_exist(out, "deck", ["pdf", "pptx"])
