"""End-to-end integration test for course synchronization."""

from pathlib import Path

from course_downloader.application import CourseDownloaderApplication


def test_full_course_sync_end_to_end(
    tmp_path: Path,
    httpx_mock,
) -> None:
    library_root = tmp_path / "library"
    manifest_path = tmp_path / "courses.yaml"

    manifest_path.write_text(
        f"""
library_root: {tmp_path / "library"}
courses:
  - id: intro
    name: Intro Course
    path: intro
    sources:
      - type: direct
        url: https://example.com/lecture.txt
""".strip(),
        encoding="utf-8",
    )

    # Only mock the HTTP boundary
    httpx_mock.add_response(
        url="https://example.com/lecture.txt",
        content=b"Hello course",
        headers={"Content-Type": "text/plain"},
    )
    httpx_mock.add_response(
        url="https://example.com/lecture.txt",
        content=b"Hello course",
        headers={"Content-Type": "text/plain"},
    )

    app = CourseDownloaderApplication(manifest_path)
    first_report = app.sync_all()
    assert first_report.failed == 0

    target = library_root / "intro" / "source" / "files" / "lecture.txt"
    assert target.exists()

    markdown_target = library_root / "intro" / "markdown" / "lecture.md"
    assert markdown_target.exists()

    second_report = app.sync_all()
    assert second_report.failed == 0
