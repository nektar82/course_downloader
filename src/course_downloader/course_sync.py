"""Course synchronization orchestration."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from types import TracebackType

from course_downloader.course_paths import CoursePaths
from course_downloader.crawler import CourseCrawler
from course_downloader.downloader import Downloader
from course_downloader.github import GitHubManager
from course_downloader.index_generator import IndexGenerator
from course_downloader.markdown_converter import MarkdownConverter
from course_downloader.models import Course, Settings, SyncReport
from course_downloader.source_handlers import (
    CoursePageSourceHandler,
    DirectSourceHandler,
    DocumentProcessor,
    GitHubSourceHandler,
    ReferenceSourceHandler,
    SourceHandler,
    YouTubeSourceHandler,
)
from course_downloader.transcript_fetcher import TranscriptFetcher
from course_downloader.youtube import YouTubeClient

LOGGER = logging.getLogger(__name__)


class CourseSynchronizer:
    """Synchronize courses by dispatching source-specific handlers."""

    def __init__(
        self,
        settings: Settings,
        *,
        downloader: Downloader | None = None,
    ) -> None:
        self.settings = settings
        self.downloader = downloader or Downloader(
            timeout_seconds=settings.timeout_seconds
        )
        self._owns_downloader = downloader is None

        converter = MarkdownConverter()
        github_handler = GitHubSourceHandler(GitHubManager())
        youtube_handler = YouTubeSourceHandler(
            settings,
            YouTubeClient(),
            TranscriptFetcher(),
        )
        processor = DocumentProcessor(settings, self.downloader, converter)
        crawler = CourseCrawler(
            self.downloader,
            request_delay_seconds=settings.request_delay_seconds,
        )
        page_handler = CoursePageSourceHandler(
            settings,
            crawler,
            processor,
            github_handler,
            youtube_handler,
        )

        self.handlers: dict[str, SourceHandler] = {
            "youtube": youtube_handler,
            "youtube_playlist": youtube_handler,
            "youtube_video": youtube_handler,
            "github": github_handler,
            "direct": DirectSourceHandler(processor),
            "course_page": page_handler,
            "reference": ReferenceSourceHandler(),
        }

    def close(self) -> None:
        """Release owned resources."""

        if self._owns_downloader:
            self.downloader.close()

    def __enter__(self) -> CourseSynchronizer:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def synchronize(self, course: Course) -> SyncReport:
        """Synchronize one course and persist a machine-readable report."""

        paths = CoursePaths(self.settings.course_download_root, course.path)
        paths.create()
        IndexGenerator().write_course_readme(
            course, paths.course_root / "README.md"
        )

        report = SyncReport()
        if not course.sources:
            report.skipped = 1
            self._write_report(course, paths, report)
            return report

        for source in course.sources:
            handler = self.handlers.get(source.type)
            if handler is None:
                report.failed += 1
                report.warnings.append(
                    f"Unsupported source type: {source.type}"
                )
                continue

            try:
                report.merge(handler.sync(source, paths))
            except Exception as exc:
                LOGGER.exception("Failed processing source %s", source.type)
                report.failed += 1
                report.warnings.append(
                    f"{source.type} source failed ({source.url}): {exc}"
                )

        self._write_report(course, paths, report)
        return report

    @staticmethod
    def _write_report(
        course: Course,
        paths: CoursePaths,
        report: SyncReport,
    ) -> None:
        payload = {
            "course_id": course.id,
            "generated_at": datetime.now(UTC).isoformat(),
            **report.to_dict(),
        }
        destination = paths.metadata / "sync-report.json"
        temp = destination.with_suffix(".json.part")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(destination)
