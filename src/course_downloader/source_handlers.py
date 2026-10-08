"""Source-specific synchronization handlers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from course_downloader.course_paths import CoursePaths
from course_downloader.crawler import CourseCrawler
from course_downloader.downloader import Downloader
from course_downloader.github import GitHubManager, repository_parts
from course_downloader.markdown_converter import MarkdownConverter
from course_downloader.models import Settings, Source, SyncReport
from course_downloader.transcript_fetcher import (
    TranscriptFetcher,
    TranscriptUnavailableError,
)
from course_downloader.transcripts import TranscriptFormatter
from course_downloader.utils import normalize_url, safe_name, url_filename
from course_downloader.whisper import WhisperTranscriber
from course_downloader.youtube import YouTubeClient

LOGGER = logging.getLogger(__name__)


class SourceHandler(Protocol):
    """Structural interface implemented by all source handlers."""

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        """Synchronize one source."""
        ...


class DocumentProcessor:
    """Download and convert document-like resources."""

    def __init__(
        self,
        settings: Settings,
        downloader: Downloader,
        converter: MarkdownConverter,
    ) -> None:
        self.settings = settings
        self.downloader = downloader
        self.converter = converter

    def process(
        self,
        url: str,
        paths: CoursePaths,
        *,
        fallback_name: str = "document",
    ) -> SyncReport:
        report = SyncReport()
        filename = url_filename(url, fallback=fallback_name, unique=True)
        destination = paths.files / filename
        markdown_destination = paths.markdown / f"{destination.stem}.md"

        if destination.exists() and not self.settings.refresh:
            report.documents_skipped += 1
        else:
            self.downloader.download_file(url, destination)
            report.documents_downloaded += 1

        if markdown_destination.exists() and not self.settings.refresh:
            return report

        converted = self.converter.convert(destination, markdown_destination)
        if converted is None:
            report.conversion_failures += 1
            report.warnings.append(f"Could not convert to Markdown: {url}")
        else:
            report.documents_converted += 1

        return report


class ReferenceSourceHandler:
    """Record-only source handler."""

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        del paths
        LOGGER.info("Reference source: %s", source.url)
        return SyncReport(skipped=1)


class GitHubSourceHandler:
    """GitHub repository source handler."""

    def __init__(self, manager: GitHubManager) -> None:
        self.manager = manager

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        if source.url is None:
            raise ValueError("GitHub source requires a URL.")

        parts = repository_parts(source.url)
        if parts is None:
            raise ValueError(f"Not a GitHub repository URL: {source.url}")

        owner, repository = parts
        destination = paths.repos / safe_name(owner) / safe_name(repository)
        self.manager.clone_or_pull(source.url, destination)
        return SyncReport(succeeded=1, repositories_updated=1)


class DirectSourceHandler:
    """Direct-file source handler."""

    def __init__(self, processor: DocumentProcessor) -> None:
        self.processor = processor

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        if source.url is None:
            raise ValueError("Direct source requires a URL.")
        report = self.processor.process(
            source.url, paths, fallback_name="download"
        )
        report.succeeded += 1
        return report


class YouTubeSourceHandler:
    """YouTube video and playlist source handler."""

    def __init__(
        self,
        settings: Settings,
        client: YouTubeClient,
        fetcher: TranscriptFetcher,
    ) -> None:
        self.settings = settings
        self.client = client
        self.fetcher = fetcher

    @staticmethod
    def _write_lecture(
        *,
        title: str,
        playlist_title: str,
        video_id: str,
        segments: list[dict[str, object]],
        formatter: TranscriptFormatter,
        raw_file: Path,
        lecture_file: Path,
        provenance: str,
    ) -> None:
        raw_file.write_text(
            json.dumps(
                {
                    "video_id": video_id,
                    "title": title,
                    "playlist": playlist_title,
                    "provenance": provenance,
                    "segments": segments,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        markdown = formatter.to_markdown(segments)
        lecture_file.write_text(
            (
                f"# {title}\n\n"
                f"Playlist: {playlist_title}\n\n"
                f"Video ID: {video_id}\n\n"
                f"Transcript source: {provenance}\n\n"
                f"## Transcript\n\n{markdown}\n"
            ),
            encoding="utf-8",
        )

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        if source.url is None:
            raise ValueError("YouTube source requires a URL.")

        report = SyncReport()
        playlist_title, entries = self.client.get_entries(source.url)
        formatter = TranscriptFormatter(
            timestamp_minutes=self.settings.timestamp_minutes,
            paragraph_chars=self.settings.paragraph_chars,
        )
        transcriber: WhisperTranscriber | None = None
        width = max(2, len(str(len(entries))))

        for position, entry in enumerate(entries, start=1):
            video_id = entry.get("id")
            if not isinstance(video_id, str) or not video_id:
                report.warnings.append(
                    f"Skipping YouTube entry without a video ID at position {position}."
                )
                continue

            report.videos_found += 1
            title = str(entry.get("title") or f"Lecture {position}")
            raw_file = (
                paths.raw_transcripts / f"{position:0{width}d}-{video_id}.json"
            )
            lecture_file = (
                paths.lectures / f"{position:0{width}d}-{video_id}.md"
            )

            if (
                raw_file.exists()
                and lecture_file.exists()
                and not self.settings.refresh
            ):
                report.transcripts_skipped += 1
                continue

            segments: list[dict[str, object]]
            provenance = "captions"
            try:
                fetched = self.fetcher.fetch(
                    video_id, list(self.settings.languages)
                )
                segments = list(fetched)
            except TranscriptUnavailableError as exc:
                if not self.settings.transcribe_if_no_captions:
                    report.transcript_failures += 1
                    report.warnings.append(f"{title}: {exc}")
                    continue

                if transcriber is None:
                    transcriber = WhisperTranscriber(
                        self.settings.whisper_model,
                        self.settings.keep_fallback_audio,
                    )
                try:
                    segments = list(
                        transcriber.transcribe(video_id, paths.fallback_audio)
                    )
                    provenance = f"whisper:{self.settings.whisper_model}"
                except Exception as whisper_exc:
                    report.transcript_failures += 1
                    report.warnings.append(
                        f"Whisper fallback failed for {title}: {whisper_exc}"
                    )
                    continue
            except Exception as exc:
                report.transcript_failures += 1
                report.warnings.append(
                    f"Transcript service failed for {title}; Whisper was not used: {exc}"
                )
                continue

            if not segments:
                report.transcript_failures += 1
                report.warnings.append(
                    f"No transcript segments produced for {title}."
                )
                continue

            self._write_lecture(
                title=title,
                playlist_title=playlist_title,
                video_id=video_id,
                segments=segments,
                formatter=formatter,
                raw_file=raw_file,
                lecture_file=lecture_file,
                provenance=provenance,
            )
            report.transcripts_created += 1

        if report.transcript_failures:
            report.failed += 1
        else:
            report.succeeded += 1
        return report


class CoursePageSourceHandler:
    """Course-page crawler source handler."""

    def __init__(
        self,
        settings: Settings,
        crawler: CourseCrawler,
        processor: DocumentProcessor,
        github_handler: GitHubSourceHandler,
        youtube_handler: YouTubeSourceHandler,
    ) -> None:
        self.settings = settings
        self.crawler = crawler
        self.processor = processor
        self.github_handler = github_handler
        self.youtube_handler = youtube_handler

    def sync(self, source: Source, paths: CoursePaths) -> SyncReport:
        if source.url is None:
            raise ValueError("Course-page source requires a URL.")

        discovered = self.crawler.discover(source)
        report = SyncReport(
            pages_fetched=len(discovered.pages),
            page_failures=len(discovered.failed_pages),
        )

        if normalize_url(source.url) in discovered.failed_pages:
            report.failed = 1
            report.warnings.append(
                f"Failed to fetch course root page: {source.url}"
            )
            return report

        if discovered.limit_reached:
            report.warnings.append(
                f"Crawler stopped at max_pages={source.max_pages} for {source.url}."
            )

        had_failure = False
        for github_url in sorted(discovered.github):
            try:
                nested = self.github_handler.sync(
                    Source(type="github", url=github_url), paths
                )
                report.merge(nested, include_source_counts=False)
            except Exception as exc:
                had_failure = True
                report.warnings.append(
                    f"GitHub sync failed for {github_url}: {exc}"
                )

        for youtube_url in sorted(discovered.youtube):
            nested = self.youtube_handler.sync(
                Source(type="youtube", url=youtube_url), paths
            )
            report.merge(nested, include_source_counts=False)
            had_failure = had_failure or bool(nested.failed)

        for document_url in sorted(discovered.documents):
            try:
                nested = self.processor.process(document_url, paths)
                report.merge(nested, include_source_counts=False)
            except Exception as exc:
                had_failure = True
                report.warnings.append(
                    f"Document processing failed for {document_url}: {exc}"
                )

        if had_failure:
            report.failed += 1
        else:
            report.succeeded += 1
        return report
