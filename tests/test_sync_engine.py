"""Sync engine tests."""

from course_downloader.models import (
    Course,
)
from course_downloader.sync_engine import (
    SyncEngine,
)


def test_sync_engine() -> None:

    engine = SyncEngine()

    course = Course(
        id="test",
        name="Test",
        path="Test",
    )

    engine.synchronize(course)
