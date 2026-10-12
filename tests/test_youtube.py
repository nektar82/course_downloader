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


@patch("course_downloader.youtube.subprocess.run")
def test_get_entries_bot_blocked_watch_url_degrades_to_single_video(
    mock_run: MagicMock,
) -> None:
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

    title, entries = YouTubeClient().get_entries(
        "https://www.youtube.com/watch?v=2xQLCXqOtdU&t=23s"
    )

    assert title == "YouTube"
    assert entries == [{"id": "2xQLCXqOtdU", "title": "Video 2xQLCXqOtdU"}]


@patch("course_downloader.youtube.subprocess.run")
def test_get_entries_bot_blocked_short_url_degrades_to_single_video(
    mock_run: MagicMock,
) -> None:
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

    _, entries = YouTubeClient().get_entries("https://youtu.be/2xQLCXqOtdU")

    assert entries[0]["id"] == "2xQLCXqOtdU"


@patch("course_downloader.youtube.subprocess.run")
def test_get_entries_playlist_failure_still_raises(
    mock_run: MagicMock,
) -> None:
    import subprocess

    import pytest

    mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

    with pytest.raises(subprocess.CalledProcessError):
        YouTubeClient().get_entries(
            "https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D"
        )
