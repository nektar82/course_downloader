"""Manifest tests."""

from course_downloader.manifest import (
    parse_courses,
    parse_sources,
)


def test_parse_sources() -> None:
    sources = parse_sources(
        [
            {
                "type": "youtube",
                "url": "https://youtube.com",
            }
        ]
    )

    assert len(sources) == 1

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
                        {
                            "type": "youtube",
                            "url": "https://youtube.com",
                        }
                    ],
                }
            ]
        }
    )

    assert len(courses) == 1

    assert courses[0].id == "python"

    assert courses[0].sources is not None

    assert len(courses[0].sources) == 1


def test_parse_course_without_sources() -> None:
    courses = parse_courses(
        {
            "courses": [
                {
                    "id": "test",
                    "name": "Test",
                    "path": "test",
                }
            ]
        }
    )

    assert len(courses) == 1

    assert courses[0].sources == []


def test_parse_source_options() -> None:
    sources = parse_sources(
        [
            {
                "type": "course_page",
                "url": "https://example.com",
                "crawl_depth": 3,
                "discover_github": False,
                "discover_youtube": False,
            }
        ]
    )

    source = sources[0]

    assert source.crawl_depth == 3

    assert source.discover_github is False

    assert source.discover_youtube is False
