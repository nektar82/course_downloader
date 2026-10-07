"""CLI tests."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from course_downloader.cli import app
from course_downloader.models import SyncReport

runner = CliRunner()


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_list_courses(
    mock_application,
    tmp_path: Path,
) -> None:
    mock_application.return_value.list_courses.return_value = []

    result = runner.invoke(
        app,
        [
            "list",
            str(tmp_path / "manifest.yml"),
        ],
    )

    assert result.exit_code == 0


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_validate(
    mock_application,
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "validate",
            str(tmp_path / "manifest.yml"),
        ],
    )

    assert result.exit_code == 0

    mock_application.return_value.validate.assert_called_once()


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync(
    mock_application,
    tmp_path: Path,
) -> None:
    mock_application.return_value.sync_all.return_value = SyncReport(
        succeeded=1
    )

    result = runner.invoke(
        app,
        [
            "sync",
            str(tmp_path / "manifest.yml"),
        ],
    )

    assert result.exit_code == 0

    mock_application.return_value.sync_all.assert_called_once()


@patch("course_downloader.cli.CourseDownloaderApplication")
def test_sync_course(
    mock_application,
    tmp_path: Path,
) -> None:
    mock_application.return_value.sync_course.return_value = SyncReport(
        succeeded=1
    )

    result = runner.invoke(
        app,
        [
            "sync-course",
            str(tmp_path / "manifest.yml"),
            "python",
        ],
    )

    assert result.exit_code == 0

    mock_application.return_value.sync_course.assert_called_once_with(
        "python",
    )


@patch("course_downloader.cli.Doctor")
def test_doctor(
    mock_doctor,
) -> None:
    result = runner.invoke(
        app,
        [
            "doctor",
        ],
    )

    assert result.exit_code == 0

    mock_doctor.return_value.run.assert_called_once()
