"""Markdown conversion."""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)

HAS_MARKITDOWN = False

try:
    from markitdown import MarkItDown

    HAS_MARKITDOWN = True

except ImportError:
    pass


class MarkdownConverter:
    """Convert documents to Markdown."""

    def __init__(
        self,
    ) -> None:
        self.converter = None

        if HAS_MARKITDOWN:
            self.converter = MarkItDown(enable_plugins=True)

    def convert(
        self,
        source: Path,
        destination: Path,
    ) -> Path | None:
        """Convert a document to Markdown."""

        if self.converter is None:
            LOGGER.warning("MarkItDown unavailable.")
            return None

        result = self.converter.convert(str(source))

        markdown = getattr(
            result,
            "markdown",
            None,
        ) or getattr(
            result,
            "text_content",
            None,
        )

        if not markdown:
            return None

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_text(
            markdown,
            encoding="utf-8",
        )

        return destination
