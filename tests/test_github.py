"""GitHub tests."""

from pathlib import Path
from unittest.mock import patch

from course_downloader.github import (
    GitHubManager,
    repository_url,
)


def test_repository_url() -> None:
    assert (
        repository_url(
            "https://github.com/user/repo",
        )
        == "https://github.com/user/repo.git"
    )


def test_repository_url_invalid() -> None:
    assert (
        repository_url(
            "https://example.com/repo",
        )
        is None
    )


@patch("course_downloader.github.subprocess.run")
def test_clone_repository(
    mock_run,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "repo"

    GitHubManager().clone_or_pull(
        "https://github.com/user/repo",
        destination,
    )

    mock_run.assert_called_once()


@patch("course_downloader.github.subprocess.run")
def test_pull_repository(
    mock_run,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "repo"

    destination.mkdir()

    (destination / ".git").mkdir()

    GitHubManager().clone_or_pull(
        "https://github.com/user/repo",
        destination,
    )

    args = mock_run.call_args[0][0]

    assert args[0] == "git"
    assert args[1] == "pull"
