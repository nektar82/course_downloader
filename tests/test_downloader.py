"""Downloader tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from course_downloader.constants import (
    MAX_DOWNLOAD_SIZE_MB,
)
from course_downloader.downloader import (
    Downloader,
)


def test_context_manager() -> None:
    with Downloader() as downloader:
        assert downloader is not None


def test_close() -> None:
    downloader = Downloader()
    downloader.close()


def test_download_file(
    tmp_path: Path,
) -> None:
    downloader = Downloader()

    response = MagicMock()

    response.headers = {
        "Content-Length": "100",
    }

    response.iter_bytes.return_value = [
        b"hello ",
        b"world",
    ]

    stream = MagicMock()

    stream.__enter__.return_value = response

    downloader.client.stream = MagicMock(
        return_value=stream,
    )

    destination = tmp_path / "test.txt"

    result = downloader.download_file(
        "https://example.com/file.txt",
        destination,
    )

    assert result == destination
    assert destination.exists()
    assert destination.read_bytes() == b"hello world"


def test_download_too_large(
    tmp_path: Path,
) -> None:
    downloader = Downloader()

    response = MagicMock()

    response.headers = {
        "Content-Length": str((MAX_DOWNLOAD_SIZE_MB + 1) * 1024 * 1024),
    }

    stream = MagicMock()

    stream.__enter__.return_value = response

    downloader.client.stream = MagicMock(
        return_value=stream,
    )

    with pytest.raises(
        ValueError,
    ):
        downloader.download_file(
            "https://example.com/file",
            tmp_path / "file",
        )
