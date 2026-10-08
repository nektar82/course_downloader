"""End-to-end integration test for direct-file synchronization."""

from pathlib import Path

import httpx

from course_downloader.application import CourseDownloaderApplication


def test_full_course_sync_end_to_end(tmp_path: Path, monkeypatch) -> None:
    course_download_root = tmp_path / "library"
    manifest_path = tmp_path / "courses.yaml"
    manifest_path.write_text(
        f"""
course_download_root: {course_download_root}
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

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.com/lecture.txt"
        return httpx.Response(
            200,
            content=b"Hello course",
            headers={"Content-Type": "text/plain"},
        )

    real_client = httpx.Client
    transport = httpx.MockTransport(handler)

    def client_factory(**kwargs):
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(
        "course_downloader.downloader.httpx.Client", client_factory
    )

    app = CourseDownloaderApplication(manifest_path)
    first_report = app.sync_all()
    assert first_report.failed == 0
    assert first_report.documents_downloaded == 1

    downloaded = list(
        (course_download_root / "intro" / "source" / "files").iterdir()
    )
    assert len(downloaded) == 1
    assert downloaded[0].read_bytes() == b"Hello course"

    second_report = app.sync_all()
    assert second_report.failed == 0
    assert second_report.documents_skipped == 1
