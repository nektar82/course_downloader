"""Manifest parsing tests."""

from course_downloader.manifest import (
    parse_courses,
)


def test_parse_course() -> None:

    manifest = {
        "courses": [
            {
                "id": "test",
                "name": "Test",
                "path": "Test",
            }
        ]
    }

    courses = parse_courses(manifest)

    assert len(courses) == 1

    assert courses[0].id == "test"
