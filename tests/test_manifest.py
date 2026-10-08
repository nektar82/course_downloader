"""Manifest tests."""

import pytest

from course_downloader.manifest import parse_courses, parse_sources


def test_parse_sources() -> None:
    sources = parse_sources(
        [{"type": "youtube", "url": "https://youtube.com/watch?v=test"}]
    )
    assert sources[0].type == "youtube"


def test_parse_courses() -> None:
    courses = parse_courses(
        {
            "courses": [
                {
                    "id": "python",
                    "name": "Python",
                    "path": "python",
                    "sources": [
                        {"type": "direct", "url": "https://example.com/a.pdf"}
                    ],
                }
            ]
        }
    )
    assert courses[0].id == "python"
    assert courses[0].sources is not None


def test_parse_course_without_sources() -> None:
    courses = parse_courses(
        {"courses": [{"id": "test", "name": "Test", "path": "test"}]}
    )
    assert courses[0].sources == []


def test_parse_source_options() -> None:
    source = parse_sources(
        [
            {
                "type": "course_page",
                "url": "https://example.com",
                "crawl_depth": 3,
                "max_pages": 25,
                "discover_github": False,
                "discover_youtube": False,
                "download_external_documents": False,
            }
        ]
    )[0]
    assert source.crawl_depth == 3
    assert source.max_pages == 25
    assert source.discover_github is False
    assert source.discover_youtube is False
    assert source.download_external_documents is False


def test_unknown_source_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown key"):
        parse_sources(
            [
                {
                    "type": "course_page",
                    "url": "https://example.com",
                    "discover_youtbe": False,
                }
            ],
            course_id="test",
        )


def test_invalid_regex_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid regex"):
        parse_sources(
            [
                {
                    "type": "course_page",
                    "url": "https://example.com",
                    "include_regex": "(",
                }
            ]
        )


def test_missing_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="url"):
        parse_sources([{"type": "direct"}])


def test_negative_crawl_depth_is_rejected() -> None:
    with pytest.raises(ValueError, match="crawl_depth"):
        parse_sources(
            [
                {
                    "type": "course_page",
                    "url": "https://example.com",
                    "crawl_depth": -1,
                }
            ]
        )
