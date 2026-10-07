"""Course synchronizer tests."""

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
def test_sync_youtube_course(
    mock_entries,
    mock_fetch,
    tmp_path: Path,
) -> None:
    mock_entries.return_value = (
        "Test Playlist",
        [
            {
                "id": "abc123",
                "title": "Video One",
            }
        ],
    )

    mock_fetch.return_value = [
        {
            "text": "hello world",
            "start": 0.0,
            "duration": 1.0,
        }
    ]

    settings = Settings(
        root=tmp_path,
    )

    course = Course(
        id="test",
        name="Test Course",
        path="test_course",
        sources=[
            Source(
                type="youtube",
                url="https://youtube.com/test",
            )
        ],
    )

    CourseSynchronizer(
        settings,
    ).synchronize(
        course,
    )

    lectures = list((tmp_path / "test_course" / "lectures").glob("*.md"))

    assert len(lectures) == 1
