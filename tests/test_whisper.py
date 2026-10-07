"""Whisper tests."""

from course_downloader.whisper import (
    WhisperTranscriber,
)


def test_creation() -> None:
    transcriber = WhisperTranscriber(
        model_name="small",
        keep_audio=False,
    )

    assert transcriber is not None
