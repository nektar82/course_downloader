"""Course synchronization."""

from __future__ import annotations

import logging

from course_downloader.course_paths import (
    CoursePaths,
)
from course_downloader.models import Course, Settings

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
    ) -> None:

        paths = CoursePaths(
            self.settings.root,
            course.path,
        )

        paths.create()

        LOGGER.info(
            "Synchronizing %s",
            course.name,
        )

        if not course.sources:
            return

        for source in course.sources:
            LOGGER.info(
                "Source type: %s",
                source.type,
            )
