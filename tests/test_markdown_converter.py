"""Markdown converter tests."""

from pathlib import Path
from unittest.mock import MagicMock

from course_downloader.markdown_converter import (
    MarkdownConverter,
)


def test_creation() -> None:
    converter = MarkdownConverter()

    assert converter is not None


def test_convert_without_markitdown(
    tmp_path: Path,
) -> None:
    converter = MarkdownConverter()

    converter.converter = None

    result = converter.convert(
        tmp_path / "input.pdf",
        tmp_path / "output.md",
    )

    assert result is None


def test_convert_success(
    tmp_path: Path,
) -> None:
    converter = MarkdownConverter()

    result = MagicMock()

    result.markdown = "# Test"

    backend = MagicMock()

    backend.convert.return_value = result

    converter.converter = backend

    output = tmp_path / "output.md"

    converted = converter.convert(
        tmp_path / "input.pdf",
        output,
    )

    assert converted == output

    assert (
        output.read_text(
            encoding="utf-8",
        )
        == "# Test"
    )


def test_convert_text_content_fallback(
    tmp_path: Path,
) -> None:
    converter = MarkdownConverter()

    result = MagicMock()

    result.markdown = None

    result.text_content = "# Fallback"

    backend = MagicMock()

    backend.convert.return_value = result

    converter.converter = backend

    output = tmp_path / "output.md"

    converted = converter.convert(
        tmp_path / "input.pdf",
        output,
    )

    assert converted == output

    assert (
        output.read_text(
            encoding="utf-8",
        )
        == "# Fallback"
    )


def test_convert_empty_result(
    tmp_path: Path,
) -> None:
    converter = MarkdownConverter()

    result = MagicMock()

    result.markdown = None

    result.text_content = None

    backend = MagicMock()

    backend.convert.return_value = result

    converter.converter = backend

    converted = converter.convert(
        tmp_path / "input.pdf",
        tmp_path / "output.md",
    )

    assert converted is None
