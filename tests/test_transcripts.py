"""Transcript tests."""

from course_downloader.transcripts import (
    TranscriptFormatter,
)


def test_markdown_generation() -> None:

    formatter = TranscriptFormatter(
        timestamp_minutes=5,
        paragraph_chars=100,
    )

    markdown = formatter.to_markdown(
        [
            {
                "text": "Hello",
                "start": 0,
            },
            {
                "text": "World",
                "start": 10,
            },
        ]
    )

    assert "###" in markdown
