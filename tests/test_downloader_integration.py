"""Downloader pipeline test."""

from pathlib import Path
from unittest.mock import MagicMock

from course_downloader.downloader import Downloader


def test_download_pipeline(tmp_path: Path) -> None:
    downloader = Downloader()
    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Length": "32"}
    response.iter_bytes.return_value = [b"abc", b"def"]
    stream = MagicMock()
    stream.__enter__.return_value = response
    downloader.client.stream = MagicMock(return_value=stream)

    destination = tmp_path / "output.txt"
    downloader.download_file("https://example.com/file", destination)
    assert destination.read_bytes() == b"abcdef"
