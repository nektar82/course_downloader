"""Integration test for the YouTube synchronization pipeline."""

from pathlib import Path
from unittest.mock import patch

from course_downloader.course_sync import (
    CourseSynchronizer,
)
from course_downloader.models import (
    Course,
    Settings,
    Source,
)


@patch("course_downloader.course_sync.TranscriptFetcher.fetch")
@patch("course_downloader.course_sync.YouTubeClient.get_entries")
def test_end_to_end_youtube_pipeline(
    mock_get_entries,
    mock_fetch,
    tmp_path: Path,
) -> None:
    mock_get_entries.return_value = (
        "Integration Playlist",
        [
            {
                "id": "vid001",
                "title": "Lecture 1",
            }
        ],
    )

    mock_fetch.return_value = [
        {
            "text": "Integration test transcript",
            "start": 0.0,
            "duration": 1.0,
        }
    ]

    settings = Settings(
        root=tmp_path,
    )

    course = Course(
        id="integration",
        name="Integration Course",
        path="integration",
        sources=[
            Source(
                type="youtube",
                url="https://youtube.com/test",
            )
        ],
    )

    synchronizer = CourseSynchronizer(
        settings,
    )

    synchronizer.synchronize(
        course,
    )

    course_root = tmp_path / "integration"

    assert (course_root / "README.md").exists()

    lecture_files = list((course_root / "lectures").glob("*.md"))

    assert len(lecture_files) == 1

    content = lecture_files[0].read_text(
        encoding="utf-8",
    )

    assert "Lecture 1" in content
    assert "Transcript" in content

    transcript_files = list(
        (course_root / "raw" / "transcripts").glob("*.json")
    )

    assert len(transcript_files) == 1
