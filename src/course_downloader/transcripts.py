"""Transcript processing."""

from __future__ import annotations

import re
from typing import Any

from course_downloader.utils import format_timestamp


class TranscriptFormatter:
    """Convert transcript segments to Markdown."""

    def __init__(
        self,
        timestamp_minutes: int,
        paragraph_chars: int,
    ) -> None:

        self.timestamp_minutes = timestamp_minutes

        self.paragraph_chars = paragraph_chars

    def to_markdown(
        self,
        segments: list[dict[str, Any]],
    ) -> str:

        interval = self.timestamp_minutes * 60

        next_heading = 0.0

        output: list[str] = []

        paragraph: list[str] = []

        paragraph_size = 0

        def flush() -> None:

            nonlocal paragraph
            nonlocal paragraph_size

            if not paragraph:
                return

            text = " ".join(paragraph)

            text = re.sub(
                r"\s+",
                " ",
                text,
            ).strip()

            if text:
                output.extend([text, ""])

            paragraph = []

            paragraph_size = 0

        for segment in segments:
            text = segment.get(
                "text",
                "",
            ).strip()

            if not text:
                continue

            start = float(
                segment.get(
                    "start",
                    0,
                )
            )

            if start >= next_heading:
                flush()

                output.extend(
                    [
                        (f"### {format_timestamp(start)}"),
                        "",
                    ]
                )

                while next_heading <= start:
                    next_heading += interval

            paragraph.append(text)

            paragraph_size += len(text)

            if paragraph_size >= self.paragraph_chars:
                flush()

        flush()

        return "\n".join(output).strip()
