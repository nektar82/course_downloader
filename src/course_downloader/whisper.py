"""Whisper transcription support."""

from __future__ import annotations

from typing import Any


class WhisperTranscriber:
    """Whisper wrapper."""

    def transcribe(
        self,
        video_id: str,
    ) -> list[dict[str, Any]]:
        """Transcribe a video.

        Placeholder implementation.
        """

        raise NotImplementedError("Whisper integration not implemented yet.")
