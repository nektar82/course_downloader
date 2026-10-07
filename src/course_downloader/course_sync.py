"""Course synchronization."""

from __future__ import annotations

import hashlib
import json
import logging
from urllib.parse import urlparse

from course_downloader.course_paths import CoursePaths
from course_downloader.crawler import (
    CourseCrawler,
)
from course_downloader.downloader import (
    Downloader,
)
from course_downloader.github import (
    GitHubManager,
)
from course_downloader.index_generator import (
    IndexGenerator,
)
from course_downloader.markdown_converter import (
    MarkdownConverter,
)
from course_downloader.models import (
    Course,
    Settings,
    Source,
    SyncReport,
)
from course_downloader.transcript_fetcher import (
    TranscriptFetcher,
)
from course_downloader.transcripts import (
    TranscriptFormatter,
)
from course_downloader.whisper import WhisperTranscriber
from course_downloader.youtube import (
    YouTubeClient,
)

LOGGER = logging.getLogger(__name__)


class CourseSynchronizer:
    """Synchronize courses."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

    def synchronize(
        self,
        course: Course,
    ) -> SyncReport:
        paths = CoursePaths(
            self.settings.root,
            course.path,
        )

        paths.create()

        IndexGenerator().write_course_readme(
            course,
            paths.course_root / "README.md",
        )

        if not course.sources:
            return SyncReport(skipped=1)

        report = SyncReport()

        for source in course.sources:
            try:
                self._process_source(
                    source,
                    paths,
                )
                report.succeeded += 1
            except Exception:
                LOGGER.exception(
                    "Failed processing source %s",
                    source.type,
                )
                report.failed += 1

        return report

    def _process_source(
        self,
        source: Source,
        paths: CoursePaths,
    ) -> None:
        source_type = source.type.lower()

        if source_type in {
            "youtube",
            "youtube_playlist",
            "youtube_video",
        }:
            self._sync_youtube(
                source,
                paths,
            )
            return

        if source_type == "github":
            self._sync_github(
                source,
                paths,
            )
            return

        if source_type == "direct":
            self._sync_direct(
                source,
                paths,
            )
            return

        if source_type == "course_page":
            self._sync_course_page(
                source,
                paths,
            )
            return

        if source_type == "reference":
            LOGGER.info(
                "Reference source: %s",
                source.url,
            )
            return

        LOGGER.warning(
            "Unsupported source type: %s",
            source.type,
        )

    def _sync_youtube(
        self,
        source: Source,
        paths: CoursePaths,
    ) -> None:
        if not source.url:
            return

        client = YouTubeClient()
        transcriber: WhisperTranscriber | None = None

        playlist_title, entries = client.get_entries(
            source.url,
        )

        formatter = TranscriptFormatter(
            timestamp_minutes=(self.settings.timestamp_minutes),
            paragraph_chars=(self.settings.paragraph_chars),
        )

        fetcher = TranscriptFetcher()

        width = max(
            2,
            len(str(len(entries))),
        )

        for position, entry in enumerate(
            entries,
            start=1,
        ):
            video_id = entry.get(
                "id",
            )

            if not video_id:
                continue

            title = entry.get("title") or f"Lecture {position}"

            try:
                segments = fetcher.fetch(
                    video_id,
                    list(self.settings.languages),
                )

            except Exception:
                if not self.settings.transcribe_if_no_captions:
                    LOGGER.exception(
                        "Transcript failed for %s",
                        title,
                    )
                    continue

                LOGGER.warning(
                    "Transcript unavailable for %s; falling back to Whisper.",
                    title,
                )
                if transcriber is None:
                    transcriber = WhisperTranscriber(
                        self.settings.whisper_model,
                        self.settings.keep_fallback_audio,
                    )

                try:
                    segments = transcriber.transcribe(
                        video_id,
                        paths.fallback_audio,
                    )
                except Exception:
                    LOGGER.exception(
                        "Whisper fallback failed for %s",
                        title,
                    )
                    continue

            if not segments:
                continue

            raw_file = paths.raw_transcripts / (
                f"{position:0{width}d}-{video_id}.json"
            )

            raw_file.write_text(
                json.dumps(
                    segments,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            markdown = formatter.to_markdown(
                segments,
            )

            lecture_file = paths.lectures / (
                f"{position:0{width}d}-{video_id}.md"
            )

            lecture_file.write_text(
                (
                    f"# {title}\n\n"
                    f"Playlist: {playlist_title}\n\n"
                    f"Video ID: {video_id}\n\n"
                    f"## Transcript\n\n"
                    f"{markdown}\n"
                ),
                encoding="utf-8",
            )

    def _sync_github(
        self,
        source: Source,
        paths: CoursePaths,
    ) -> None:
        if not source.url:
            return

        parsed = urlparse(source.url)
        repo_name = parsed.path.rstrip("/").split("/")[-1].replace(".git", "")
        destination = paths.repos / repo_name

        GitHubManager().clone_or_pull(
            source.url,
            destination,
        )

    def _sync_direct(
        self,
        source: Source,
        paths: CoursePaths,
    ) -> None:
        if not source.url:
            return

        downloader = Downloader()

        parsed = urlparse(source.url)
        filename = parsed.path.rsplit("/", 1)[-1] or "download"
        if not filename:
            filename = "download"

        destination = paths.files / filename

        file_path = downloader.download_file(
            source.url,
            destination,
        )

        MarkdownConverter().convert(
            file_path,
            (paths.markdown / f"{file_path.stem}.md"),
        )

    def _sync_course_page(
        self,
        source: Source,
        paths: CoursePaths,
    ) -> None:
        if not source.url:
            return

        downloader = Downloader()

        crawler = CourseCrawler(
            downloader,
        )

        discovered = crawler.discover(
            source,
        )

        for github_url in discovered["github"]:
            parsed = urlparse(github_url)
            repo_name = (
                parsed.path.rstrip("/").split("/")[-1].replace(".git", "")
            )
            destination = paths.repos / repo_name

            GitHubManager().clone_or_pull(
                github_url,
                destination,
            )

        for youtube_url in discovered["youtube"]:
            self._sync_youtube(
                Source(
                    type="youtube",
                    url=youtube_url,
                ),
                paths,
            )

        for document_url in discovered["documents"]:
            parsed = urlparse(document_url)
            filename = parsed.path.rsplit("/", 1)[-1] or "document"

            destination = paths.files / filename
            destination = destination.with_name(
                hashlib.sha256(document_url.encode("utf-8")).hexdigest()[:12]
                + destination.suffix
            )

            file_path = downloader.download_file(
                document_url,
                destination,
            )

            MarkdownConverter().convert(
                file_path,
                (paths.markdown / f"{file_path.stem}.md"),
            )
