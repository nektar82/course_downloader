"""Application data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class Source:
    """Course source definition."""

    type: str

    url: str | None = None

    label: str | None = None

    crawl_depth: int = 1

    download_documents: bool = True

    discover_youtube: bool = True

    discover_github: bool = True

    allowed_domains: list[str] | None = None

    include_regex: str | None = None

    exclude_regex: str | None = None

    page_include_regex: str | None = None

    document_link_regex: str | None = None


@dataclass(slots=True, frozen=True)
class Course:
    """Course definition."""

    id: str

    name: str

    path: str

    status: str | None = None

    why: str | None = None

    tags: list[str] | None = None

    sources: list[Source] | None = None


@dataclass(slots=True)
class Settings:
    """Application settings."""

    root: Path

    timestamp_minutes: int = 5

    paragraph_chars: int = 700

    languages: tuple[str, ...] = (
        "en",
        "en-US",
        "en-GB",
    )

    transcribe_if_no_captions: bool = False

    whisper_model: str = "small"

    keep_fallback_audio: bool = False

    request_delay_seconds: float = 0.15

    timeout_seconds: int = 45

    refresh: bool = False
