"""Markdown conversion tests."""

from course_downloader.markdown_converter import (
    MarkdownConverter,
)


def test_converter_creation() -> None:

    converter = MarkdownConverter()

    assert converter is not None
