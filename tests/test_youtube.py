"""YouTube tests."""

from course_downloader.youtube import (
    YouTubeClient,
)


def test_client_creation() -> None:

    client = YouTubeClient()

    assert client is not None
