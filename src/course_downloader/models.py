"""Application data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from course_downloader.constants import DEFAULT_MAX_PAGES

SourceType = Literal[
    "youtube",
    "youtube_playlist",
    "youtube_video",
    "github",
    "direct",
    "course_page",
    "reference",
]


@dataclass(slots=True, frozen=True)
class Source:
    """Course source definition."""

    type: SourceType
    url: str | None = None
    label: str | None = None
    crawl_depth: int = 1
    max_pages: int = DEFAULT_MAX_PAGES
    download_documents: bool = True
    download_external_documents: bool = True
    discover_youtube: bool = True
    discover_github: bool = True
    allowed_domains: list[str] | None = None
    include_regex: str | None = None
    exclude_regex: str | None = None
    page_include_regex: str | None = None
    document_link_regex: str | None = None


@dataclass(slots=True)
class CrawlResult:
    """Crawler discovery result."""

    pages: set[str] = field(default_factory=set)
    failed_pages: set[str] = field(default_factory=set)
    youtube: set[str] = field(default_factory=set)
    github: set[str] = field(default_factory=set)
    documents: set[str] = field(default_factory=set)
    limit_reached: bool = False

    def __getitem__(self, key: str) -> set[str]:
        value = getattr(self, key)
        if not isinstance(value, set):
            raise KeyError(key)
        return value


@dataclass(slots=True)
class SyncReport:
    """Aggregated synchronization outcome."""

    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    pages_fetched: int = 0
    page_failures: int = 0
    documents_downloaded: int = 0
    documents_converted: int = 0
    documents_skipped: int = 0
    conversion_failures: int = 0
    videos_found: int = 0
    transcripts_created: int = 0
    transcripts_skipped: int = 0
    transcript_failures: int = 0
    repositories_updated: int = 0

    @property
    def is_success(self) -> bool:
        return self.failed == 0

    def merge(
        self,
        other: SyncReport,
        *,
        include_source_counts: bool = True,
    ) -> None:
        """Merge another report into this one."""

        if include_source_counts:
            self.succeeded += other.succeeded
            self.skipped += other.skipped
            self.failed += other.failed

        self.warnings.extend(other.warnings)
        self.pages_fetched += other.pages_fetched
        self.page_failures += other.page_failures
        self.documents_downloaded += other.documents_downloaded
        self.documents_converted += other.documents_converted
        self.documents_skipped += other.documents_skipped
        self.conversion_failures += other.conversion_failures
        self.videos_found += other.videos_found
        self.transcripts_created += other.transcripts_created
        self.transcripts_skipped += other.transcripts_skipped
        self.transcript_failures += other.transcript_failures
        self.repositories_updated += other.repositories_updated

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""

        return asdict(self)


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

    course_download_root: Path
    timestamp_minutes: int = 5
    paragraph_chars: int = 700
    languages: tuple[str, ...] = ("en", "en-US", "en-GB")
    transcribe_if_no_captions: bool = False
    whisper_model: str = "small"
    keep_fallback_audio: bool = False
    request_delay_seconds: float = 0.15
    timeout_seconds: int = 45
    refresh: bool = False
