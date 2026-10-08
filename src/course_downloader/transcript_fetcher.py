"""Transcript retrieval."""

from __future__ import annotations

from typing import Any

HAS_YOUTUBE_TRANSCRIPTS = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi

    HAS_YOUTUBE_TRANSCRIPTS = True
except ImportError:
    pass


class TranscriptUnavailableError(RuntimeError):
    """Raised when a video has no usable transcript."""


class TranscriptFetcher:
    """Fetch YouTube transcripts."""

    def fetch(
        self,
        video_id: str,
        languages: list[str],
    ) -> list[dict[str, Any]]:
        """Retrieve transcript segments."""

        transcript = self._choose_transcript(video_id, languages)
        fetched = transcript.fetch(preserve_formatting=True)
        return self._segments_to_dicts(fetched)

    def _choose_transcript(
        self,
        video_id: str,
        languages: list[str],
    ) -> Any:
        """Select the best available transcript.

        Failures while listing/fetching transcripts propagate. Only the absence
        of a suitable transcript is converted to TranscriptUnavailableError so
        callers do not run Whisper for transient API/network failures.
        """

        if not HAS_YOUTUBE_TRANSCRIPTS:
            raise RuntimeError("youtube-transcript-api is not installed.")

        transcript_list = YouTubeTranscriptApi().list(video_id)

        for method_name in (
            "find_manually_created_transcript",
            "find_generated_transcript",
            "find_transcript",
        ):
            method = getattr(transcript_list, method_name, None)
            if method is None:
                continue
            try:
                return method(languages)
            except Exception as exc:
                if exc.__class__.__name__ != "NoTranscriptFound":
                    raise

        available = list(transcript_list)
        for transcript in available:
            if getattr(transcript, "is_translatable", False):
                try:
                    return transcript.translate("en")
                except Exception:
                    continue

        if available:
            return available[0]

        raise TranscriptUnavailableError("No transcript is available.")

    @staticmethod
    def _segments_to_dicts(fetched: Any) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        for segment in fetched:
            if isinstance(segment, dict):
                segments.append(
                    {
                        "text": segment.get("text", ""),
                        "start": float(segment.get("start", 0.0)),
                        "duration": float(segment.get("duration", 0.0)),
                    }
                )
                continue

            segments.append(
                {
                    "text": getattr(segment, "text", ""),
                    "start": float(getattr(segment, "start", 0.0)),
                    "duration": float(getattr(segment, "duration", 0.0)),
                }
            )

        return segments
