"""Course synchronizer tests."""

from pathlib import Path
from unittest.mock import Mock

from course_downloader.course_sync import CourseSynchronizer
from course_downloader.models import Course, Settings, Source, SyncReport


def test_sync_dispatches_and_persists_report(tmp_path: Path) -> None:
    downloader = Mock()
    settings = Settings(course_download_root=tmp_path)
    synchronizer = CourseSynchronizer(settings, downloader=downloader)
    handler = Mock()
    handler.sync.return_value = SyncReport(succeeded=1, documents_downloaded=1)
    synchronizer.handlers["direct"] = handler

    course = Course(
        id="test",
        name="Test Course",
        path="test_course",
        sources=[Source(type="direct", url="https://example.com/a.txt")],
    )
    report = synchronizer.synchronize(course)

    assert report.succeeded == 1
    assert report.documents_downloaded == 1
    assert (tmp_path / "test_course" / "metadata" / "sync-report.json").exists()
