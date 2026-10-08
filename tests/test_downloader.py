"""Downloader tests."""

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from course_downloader.downloader import Downloader


def _stream(response: MagicMock) -> MagicMock:
    stream = MagicMock()
    stream.__enter__.return_value = response
    return stream


def test_context_manager() -> None:
    with Downloader() as downloader:
        assert downloader is not None


def test_download_file(tmp_path: Path) -> None:
    downloader = Downloader()
    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Length": "11"}
    response.iter_bytes.return_value = [b"hello ", b"world"]
    downloader.client.stream = MagicMock(return_value=_stream(response))

    destination = tmp_path / "test.txt"
    result = downloader.download_file(
        "https://example.com/file.txt", destination
    )
    assert result == destination
    assert destination.read_bytes() == b"hello world"


def test_stream_limit_without_content_length(tmp_path: Path) -> None:
    downloader = Downloader(max_size_mb=1)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.iter_bytes.return_value = [b"x" * (1024 * 1024 + 1)]
    downloader.client.stream = MagicMock(return_value=_stream(response))

    destination = tmp_path / "large.bin"
    with pytest.raises(ValueError, match="size limit"):
        downloader.download_file("https://example.com/large.bin", destination)
    assert not destination.exists()
    assert not (tmp_path / "large.bin.part").exists()


def test_interrupted_download_leaves_no_final_file(tmp_path: Path) -> None:
    downloader = Downloader(retries=0)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.iter_bytes.side_effect = httpx.ReadError("connection lost")
    downloader.client.stream = MagicMock(return_value=_stream(response))

    destination = tmp_path / "broken.bin"
    with pytest.raises(httpx.ReadError):
        downloader.download_file("https://example.com/broken.bin", destination)
    assert not destination.exists()
    assert not (tmp_path / "broken.bin.part").exists()
