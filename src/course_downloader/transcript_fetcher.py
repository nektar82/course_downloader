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

        if not HAS_YOUTUBE_TRANSCRIPTS:
            raise RuntimeError("youtube-transcript-api is not installed.")

        api = YouTubeTranscriptApi()

        transcript_list = api.list(video_id)

        transcript = transcript_list.find_transcript(languages)

        fetched = transcript.fetch()

        return [
            {
                "text": item.text,
                "start": float(item.start),
                "duration": float(item.duration),
            }
            for item in fetched
        ]
