"""Transcript retrieval."""

from __future__ import annotations

from typing import Any

HAS_YOUTUBE_TRANSCRIPTS = False

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
    )

    HAS_YOUTUBE_TRANSCRIPTS = True

except ImportError:
    pass


class TranscriptFetcher:
    """Fetch YouTube transcripts."""

    def fetch(
        self,
        video_id: str,
        languages: list[str],
    ) -> list[dict[str, Any]]:
        """Retrieve transcript segments."""

        transcript = self._choose_transcript(
            video_id,
            languages,
        )

        fetched = transcript.fetch(
            preserve_formatting=True,
        )

        return self._segments_to_dicts(
            fetched,
        )

    def _choose_transcript(
        self,
        video_id: str,
        languages: list[str],
    ) -> Any:
        """Select best available transcript."""

        if not HAS_YOUTUBE_TRANSCRIPTS:
            raise RuntimeError("youtube-transcript-api is not installed.")

        api = YouTubeTranscriptApi()

        transcript_list = api.list(
            video_id,
        )

        for method_name in (
            "find_manually_created_transcript",
            "find_generated_transcript",
            "find_transcript",
        ):
            method = getattr(
                transcript_list,
                method_name,
                None,
            )

            if method is None:
                continue

            try:
                return method(
                    languages,
                )
            except Exception:
                pass

        for transcript in transcript_list:
            try:
                if getattr(
                    transcript,
                    "is_translatable",
                    False,
                ):
                    return transcript.translate(
                        "en",
                    )
            except Exception:
                pass

            return transcript

        raise RuntimeError("No transcript is available.")

    @staticmethod
    def _segments_to_dicts(
        fetched: Any,
    ) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []

        for segment in fetched:
            if isinstance(
                segment,
                dict,
            ):
                segments.append(
                    {
                        "text": segment.get(
                            "text",
                            "",
                        ),
                        "start": float(
                            segment.get(
                                "start",
                                0.0,
                            )
                        ),
                        "duration": float(
                            segment.get(
                                "duration",
                                0.0,
                            )
                        ),
                    }
                )

                continue

            segments.append(
                {
                    "text": getattr(
                        segment,
                        "text",
                        "",
                    ),
                    "start": float(
                        getattr(
                            segment,
                            "start",
                            0.0,
                        )
                    ),
                    "duration": float(
                        getattr(
                            segment,
                            "duration",
                            0.0,
                        )
                    ),
                }
            )

        return segments
