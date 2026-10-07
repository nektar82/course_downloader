"""Whisper transcription support."""

from __future__ import annotations

import shutil
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import Any


class WhisperTranscriber:
    """Whisper wrapper."""

    def __init__(
        self,
        model_name: str,
        keep_audio: bool,
    ) -> None:
        self.model_name = model_name
        self.keep_audio = keep_audio
        self._model: Any | None = None

    def transcribe(
        self,
        video_id: str,
        audio_directory: Path,
    ) -> list[dict[str, Any]]:
        """Transcribe a YouTube video."""

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg is required for Whisper transcription.")

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper is not installed.") from exc

        audio_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        template = audio_directory / f"{video_id}.%(ext)s"

        subprocess.run(
            [
                "yt-dlp",
                "-f",
                "bestaudio/best",
                "--extract-audio",
                "--audio-format",
                "wav",
                "-o",
                str(template),
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        audio_path = audio_directory / f"{video_id}.wav"

        if not audio_path.exists():
            matches = list(audio_directory.glob(f"{video_id}.*"))

            if not matches:
                raise RuntimeError("yt-dlp did not produce audio.")

            audio_path = matches[0]

        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                device="auto",
                compute_type="auto",
            )

        segments, _ = self._model.transcribe(
            str(audio_path),
            vad_filter=True,
        )

        results = [
            {
                "text": segment.text.strip(),
                "start": float(segment.start),
                "duration": float(segment.end - segment.start),
            }
            for segment in segments
        ]

        if not self.keep_audio:
            with suppress(OSError):
                audio_path.unlink()

        return results
