"""CLI tests."""

from typer.testing import CliRunner

from course_downloader.cli import app

runner = CliRunner()


def test_app_exists() -> None:
    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0
