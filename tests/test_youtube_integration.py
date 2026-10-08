"""YouTube synchronization pipeline test."""

from pathlib import Path
from unittest.mock import patch

from course_downloader.course_sync import CourseSynchronizer
from course_downloader.models import Course, Settings, Source


@patch("course_downloader.source_handlers.TranscriptFetcher.fetch")
@patch("course_downloader.source_handlers.YouTubeClient.get_entries")
def test_youtube_pipeline(mock_get_entries, mock_fetch, tmp_path: Path) -> None:
    mock_get_entries.return_value = (
        "Integration Playlist",
        [{"id": "vid001", "title": "Lecture 1"}],
    )
    mock_fetch.return_value = [
        {"text": "Integration test transcript", "start": 0.0, "duration": 1.0}
    ]

    course = Course(
        id="integration",
        name="Integration Course",
        path="integration",
        sources=[Source(type="youtube", url="https://youtube.com/test")],
    )
    with CourseSynchronizer(
        Settings(course_download_root=tmp_path)
    ) as synchronizer:
        report = synchronizer.synchronize(course)

    course_root = tmp_path / "integration"
    assert report.failed == 0
    assert report.transcripts_created == 1
    lecture_files = list((course_root / "lectures").glob("*.md"))
    assert len(lecture_files) == 1
    assert "Lecture 1" in lecture_files[0].read_text(encoding="utf-8")
