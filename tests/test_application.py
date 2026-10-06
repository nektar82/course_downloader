"""Application tests."""

from pathlib import Path

from course_downloader.application import (
    CourseDownloaderApplication,
)


def test_application_loads(
    tmp_path: Path,
) -> None:

    manifest = tmp_path / "courses.yaml"

    manifest.write_text(
        """
courses:
  - id: test
    name: Test
    path: Test
""",
        encoding="utf-8",
    )

    application = CourseDownloaderApplication(manifest)

    assert len(application.courses) == 1
