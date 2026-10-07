"""Markdown converter integration."""

from pathlib import Path
from unittest.mock import MagicMock

from course_downloader.markdown_converter import (
    MarkdownConverter,
)


def test_conversion_pipeline(
    tmp_path: Path,
) -> None:
    converter = MarkdownConverter()

    result = MagicMock()

    result.markdown = "# Converted\n\nContent"

    backend = MagicMock()

    backend.convert.return_value = result

    converter.converter = backend

    output = tmp_path / "result.md"

    converter.convert(
        tmp_path / "input.pdf",
        output,
    )

    assert output.exists()

    assert "# Converted" in output.read_text(
        encoding="utf-8",
    )
