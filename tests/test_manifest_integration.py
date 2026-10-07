"""Manifest integration."""

from course_downloader.manifest import (
    parse_courses,
)


def test_manifest_to_course_model() -> None:
    manifest = {
        "courses": [
            {
                "id": "course",
                "name": "Course",
                "path": "course",
                "status": "active",
                "why": "testing",
                "sources": [
                    {
                        "type": "youtube",
                        "url": "https://youtube.com",
                    }
                ],
            }
        ]
    }

    courses = parse_courses(
        manifest,
    )

    assert len(courses) == 1

    course = courses[0]

    assert course.id == "course"

    assert course.status == "active"

    assert course.why == "testing"

    assert course.sources is not None

    assert course.sources[0].type == "youtube"
