"""Utility helpers."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse

_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_name(text: str, limit: int = 140) -> str:
    """Create a filesystem-safe name."""

    text = unquote(text)
    text = _INVALID_FILE_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip().rstrip(". ")

    if not text:
        return "untitled"

    stem = Path(text).stem.upper()
    if stem in _WINDOWS_RESERVED:
        text = f"_{text}"

    return text[:limit]


def slug(text: str, limit: int = 100) -> str:
    """Convert text to a URL-friendly slug."""

    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return (text or "item")[:limit]


def normalize_url(url: str) -> str:
    """Remove fragments from URLs."""

    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment=""))


def url_filename(
    url: str,
    *,
    fallback: str = "download",
    unique: bool = True,
) -> str:
    """Create a stable filesystem-safe filename for a URL."""

    parsed = urlparse(url)
    raw_name = parsed.path.rsplit("/", 1)[-1] or fallback
    name = safe_name(raw_name)
    path = Path(name)

    if not unique:
        return name

    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    suffix = path.suffix
    stem = path.stem or fallback
    return f"{safe_name(stem)}-{digest}{suffix}"


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""

    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"
