"""YouTube tests."""

from unittest.mock import MagicMock, patch

from course_downloader.youtube import (
    YouTubeClient,
)


@patch("course_downloader.youtube.subprocess.run")
def test_get_entries_playlist(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value.stdout = """
    {
        "title": "Test Playlist",
        "entries": [
            {
                "id": "abc123"
            },
            {
                "id": "def456"
            }
        ]
    }
    """

    title, entries = YouTubeClient().get_entries("playlist")

    assert title == "Test Playlist"
    assert len(entries) == 2


@patch("course_downloader.youtube.subprocess.run")
def test_get_entries_video(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value.stdout = """
    {
        "id": "abc123",
        "title": "Video"
    }
    """

    title, entries = YouTubeClient().get_entries("video")

    assert title == "Video"
    assert len(entries) == 1
