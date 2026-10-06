"""Downloader tests."""

from course_downloader.downloader import (
    Downloader,
)


def test_downloader_creation() -> None:

    downloader = Downloader()

    downloader.close()


def test_context_manager() -> None:

    with Downloader() as downloader:
        assert downloader is not None
