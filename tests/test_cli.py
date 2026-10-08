"""CLI tests."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from course_downloader.cli import app
from course_downloader.models import SyncReport

runner = CliRunner()


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync_success(mock_application, tmp_path: Path) -> None:
    mock_application.return_value.sync_all.return_value = SyncReport(
        succeeded=1
    )
    result = runner.invoke(app, ["sync", str(tmp_path / "manifest.yml")])
    assert result.exit_code == 0


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync_failure_returns_nonzero(mock_application, tmp_path: Path) -> None:
    mock_application.return_value.sync_all.return_value = SyncReport(failed=1)
    result = runner.invoke(app, ["sync", str(tmp_path / "manifest.yml")])
    assert result.exit_code == 1


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync_filters_and_course_download_root(
    mock_application, tmp_path: Path
) -> None:
    mock_application.return_value.sync_all.return_value = SyncReport(
        succeeded=1
    )
    course_download_root = tmp_path / "library"
    result = runner.invoke(
        app,
        [
            "sync",
            str(tmp_path / "manifest.yml"),
            "--course",
            "course-a",
            "--tag",
            "ai",
            "--course-download-root",
            str(course_download_root),
            "--refresh",
        ],
    )
    assert result.exit_code == 0
    mock_application.assert_called_once_with(
        tmp_path / "manifest.yml",
        course_download_root_override=course_download_root,
        refresh=True,
    )
    mock_application.return_value.sync_all.assert_called_once_with(
        course_ids={"course-a"},
        tags={"ai"},
    )


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync_course_legacy_command(mock_application, tmp_path: Path) -> None:
    mock_application.return_value.sync_course.return_value = SyncReport(
        succeeded=1
    )
    result = runner.invoke(
        app,
        ["sync-course", str(tmp_path / "manifest.yml"), "python"],
    )
    assert result.exit_code == 0
    mock_application.return_value.sync_course.assert_called_once_with("python")


@patch("course_downloader.cli.Doctor")
def test_doctor(mock_doctor) -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    mock_doctor.return_value.run.assert_called_once()
