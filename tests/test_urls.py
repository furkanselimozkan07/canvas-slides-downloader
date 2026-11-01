import pytest

from slides_downloader.urls import is_google_slides_url, name_from_url, slide_id, to_embed_url

PUBLISHED = "https://docs.google.com/presentation/d/e/2PACX-abc123"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (PUBLISHED + "/embed?start=false&loop=false", True),
        ("https://docs.google.com/presentation/d/1AbC/edit", True),
        ("https://docs.google.com/document/d/1AbC/edit", False),
        ("https://canvas.example.edu/courses/1/pages/lecture-02", False),
    ],
)
def test_is_google_slides_url(url, expected):
    assert is_google_slides_url(url) is expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (PUBLISHED + "/embed?start=false&delayms=3000", PUBLISHED + "/embed?start=false&delayms=3000"),
        (PUBLISHED + "/pub?start=false", PUBLISHED + "/embed"),
        (PUBLISHED + "/pubembed", PUBLISHED + "/embed"),
        (PUBLISHED, PUBLISHED + "/embed"),
        (
            "https://docs.google.com/presentation/d/1AbC/edit#slide=id.p1",
            "https://docs.google.com/presentation/d/1AbC/embed",
        ),
        ("https://canvas.example.edu/courses/1", "https://canvas.example.edu/courses/1"),
    ],
)
def test_to_embed_url(url, expected):
    assert to_embed_url(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (PUBLISHED + "/embed?slide=id.p3", "id.p3"),
        (PUBLISHED + "/embed#slide=id.g12ab_0_5", "id.g12ab_0_5"),
        (PUBLISHED + "/embed?start=false", None),
    ],
)
def test_slide_id(url, expected):
    assert slide_id(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://canvas.example.edu/courses/42/pages/lecture-02-slides", "lecture-02-slides"),
        ("https://canvas.example.edu/courses/42/pages/lecture 2 (intro)/", "lecture_2_intro"),
        (PUBLISHED + "/embed", "2PACX-abc123"),
        ("https://example.edu/", "slides"),
    ],
)
def test_name_from_url(url, expected):
    assert name_from_url(url) == expected


def test_parse_url_list_ignores_comments_blanks_and_duplicates():
    from slides_downloader.urls import parse_url_list

    lines = [
        "# week 1",
        "https://a.edu/p/1   # lecture 1",
        "",
        "  https://a.edu/p/2  ",
        "https://a.edu/p/1",
        "https://a.edu/p/3#section",
    ]
    assert parse_url_list(lines) == ["https://a.edu/p/1", "https://a.edu/p/2", "https://a.edu/p/3#section"]
