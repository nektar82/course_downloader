"""Application orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from course_downloader.config import build_settings, load_manifest
from course_downloader.course_sync import CourseSynchronizer
from course_downloader.manifest import parse_courses
from course_downloader.models import Course, Settings

LOGGER = logging.getLogger(__name__)


class CourseDownloaderApplication:
    """Main application façade.

    Coordinates configuration loading,
    validation, synchronization,
    crawling, indexing and reporting.
    """

    def __init__(
        self,
        manifest_path: Path,
    ) -> None:
        """Initialize the application.

        Args:
            manifest_path: Path to the manifest file.
        """
        self.manifest_path = manifest_path

        self.manifest = load_manifest(manifest_path)

        self.settings: Settings = build_settings(self.manifest)

        self.courses: list[Course] = parse_courses(self.manifest)

    def list_courses(self) -> list[Course]:
        """Return all configured courses."""

        return self.courses

    def get_course(
        self,
        course_id: str,
    ) -> Course:
        """Get a course by identifier."""

        for course in self.courses:
            if course.id == course_id:
                return course

        raise ValueError(f"Unknown course id: {course_id}")

    def validate(
        self,
    ) -> None:
        """Validate manifest integrity."""

        seen_ids: set[str] = set()

        for course in self.courses:
            if course.id in seen_ids:
                raise ValueError(f"Duplicate course id: {course.id}")

            seen_ids.add(course.id)

    def doctor(
        self,
    ) -> None:
        """Run diagnostics."""

        LOGGER.info("Running diagnostics.")

    def sync_all(
        self,
    ) -> None:
        """Synchronize all configured courses."""

        self.validate()

        synchronizer = CourseSynchronizer(self.settings)

        LOGGER.info(
            "Synchronizing %d courses.",
            len(self.courses),
        )

        for course in self.courses:
            synchronizer.synchronize(course)

    def sync_course(
        self,
        course_id: str,
    ) -> None:
        """Synchronize a single course."""

        course = self.get_course(course_id)

        synchronizer = CourseSynchronizer(self.settings)

        synchronizer.synchronize(course)
