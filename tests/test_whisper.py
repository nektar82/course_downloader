"""Whisper tests."""

from course_downloader.whisper import (
    WhisperTranscriber,
)


def test_creation() -> None:

    transcriber = WhisperTranscriber()

    assert transcriber is not None
