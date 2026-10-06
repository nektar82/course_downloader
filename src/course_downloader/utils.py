"""Utility helpers."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse, urlunparse

_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(
    text: str,
    limit: int = 140,
) -> str:
    """Create a filesystem-safe name."""

    text = unquote(text)

    text = _INVALID_FILE_CHARS.sub("", text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    text = text.rstrip(". ")

    if not text:
        return "untitled"

    return text[:limit]


def slug(
    text: str,
    limit: int = 100,
) -> str:
    """Convert text to a URL-friendly slug."""

    text = text.lower()

    text = re.sub(
        r"[^\w\s-]",
        "",
        text,
    )

    text = re.sub(
        r"[\s_-]+",
        "-",
        text,
    )

    text = text.strip("-")

    return (text or "item")[:limit]


def normalize_url(url: str) -> str:
    """Remove fragments from URLs."""

    parsed = urlparse(url)

    parsed = parsed._replace(fragment="")

    return urlunparse(parsed)


def format_timestamp(
    seconds: float,
) -> str:
    """Format seconds as HH:MM:SS."""

    total = max(
        0,
        int(seconds),
    )

    hours, remainder = divmod(
        total,
        3600,
    )

    minutes, secs = divmod(
        remainder,
        60,
    )

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"
