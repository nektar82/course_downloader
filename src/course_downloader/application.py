"""Application orchestration."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from course_downloader.config import build_settings, load_manifest
from course_downloader.course_sync import CourseSynchronizer
from course_downloader.manifest import parse_courses
from course_downloader.models import Course, Settings, SyncReport

LOGGER = logging.getLogger(__name__)


class CourseDownloaderApplication:
    """Main application façade."""

    def __init__(
        self,
        manifest_path: Path,
        *,
        course_download_root_override: Path | None = None,
        refresh: bool = False,
    ) -> None:
        self.manifest_path = manifest_path
        self.manifest = load_manifest(manifest_path)
        self.settings: Settings = build_settings(
            self.manifest,
            course_download_root_override=course_download_root_override,
            refresh=refresh,
        )
        self.courses: list[Course] = parse_courses(self.manifest)

    def list_courses(self) -> list[Course]:
        """Return all configured courses."""

        return self.courses

    def get_course(self, course_id: str) -> Course:
        """Get a course by identifier."""

        for course in self.courses:
            if course.id == course_id:
                return course
        raise ValueError(f"Unknown course id: {course_id}")

    def validate(self) -> None:
        """Validate cross-course manifest integrity."""

        seen_ids: set[str] = set()
        seen_paths: set[str] = set()
        for course in self.courses:
            if course.id in seen_ids:
                raise ValueError(f"Duplicate course id: {course.id}")
            if course.path in seen_paths:
                raise ValueError(f"Duplicate course path: {course.path}")
            seen_ids.add(course.id)
            seen_paths.add(course.path)

    def select_courses(
        self,
        *,
        course_ids: set[str] | None = None,
        tags: set[str] | None = None,
    ) -> list[Course]:
        """Select courses by ID and/or tag."""

        selected = self.courses
        if course_ids:
            known_ids = {course.id for course in self.courses}
            unknown = sorted(course_ids - known_ids)
            if unknown:
                raise ValueError(f"Unknown course id(s): {', '.join(unknown)}")
            selected = [
                course for course in selected if course.id in course_ids
            ]

        if tags:
            selected = [
                course
                for course in selected
                if tags.intersection(course.tags or [])
            ]

        if (course_ids or tags) and not selected:
            raise ValueError("No courses matched the requested filters.")
        return selected

    def _failed_count(self, course: Course) -> int:
        """Return the failed-operation count from the course's latest report."""

        report_path = (
            self.settings.course_download_root
            / course.path
            / "metadata"
            / "sync-report.json"
        )
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            return int(payload.get("failed", 0))
        except (OSError, ValueError):
            return 0

    def _prioritize_failures(self, courses: list[Course]) -> list[Course]:
        """Order courses so those with outstanding failures run first.

        Restarts (e.g. after a VM reboot) would otherwise re-walk clean
        courses from the top of the manifest while courses needing retries
        starve. Python's sort is stable, so manifest order is preserved
        among courses with equal failure counts.
        """

        prioritized = sorted(courses, key=lambda c: -self._failed_count(c))
        needs_work = sum(1 for c in courses if self._failed_count(c) > 0)
        if needs_work:
            LOGGER.info(
                "Prioritizing %d courses with outstanding failures first.",
                needs_work,
            )
        return prioritized

    def sync_all(
        self,
        *,
        course_ids: set[str] | None = None,
        tags: set[str] | None = None,
    ) -> SyncReport:
        """Synchronize selected configured courses."""

        self.validate()
        selected = self.select_courses(course_ids=course_ids, tags=tags)
        selected = self._prioritize_failures(selected)
        report = SyncReport()
        LOGGER.info("Synchronizing %d courses.", len(selected))

        with CourseSynchronizer(self.settings) as synchronizer:
            for course in selected:
                report.merge(synchronizer.synchronize(course))
        return report

    def sync_course(self, course_id: str) -> SyncReport:
        """Synchronize a single course."""

        self.validate()
        course = self.get_course(course_id)
        with CourseSynchronizer(self.settings) as synchronizer:
            return synchronizer.synchronize(course)
