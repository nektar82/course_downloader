"""Synchronization engine."""

from __future__ import annotations

import logging

from course_downloader.models import Course

LOGGER = logging.getLogger(__name__)


class SyncEngine:
    """Course synchronization."""

    def synchronize(
        self,
        course: Course,
    ) -> None:

        LOGGER.info(
            "Synchronizing %s",
            course.name,
        )
