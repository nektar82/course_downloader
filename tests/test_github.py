"""GitHub tests."""

from course_downloader.github import (
    repository_url,
)


def test_repository_url() -> None:

    result = repository_url("https://github.com/user/repo")

    assert result == "https://github.com/user/repo.git"


def test_repository_url_invalid() -> None:

    result = repository_url("https://example.com/repo")

    assert result is None
