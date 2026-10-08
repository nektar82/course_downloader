"""Application orchestration."""

from __future__ import annotations

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

    def sync_all(
        self,
        *,
        course_ids: set[str] | None = None,
        tags: set[str] | None = None,
    ) -> SyncReport:
        """Synchronize selected configured courses."""

        self.validate()
        selected = self.select_courses(course_ids=course_ids, tags=tags)
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
