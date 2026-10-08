"""GitHub integration."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)

GITHUB_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/#?]+)",
    re.IGNORECASE,
)


def repository_parts(url: str) -> tuple[str, str] | None:
    """Return the owner and repository for a GitHub URL."""

    match = GITHUB_RE.match(url)
    if not match:
        return None
    return match.group(1), match.group(2).removesuffix(".git")


def repository_url(url: str) -> str | None:
    """Convert a GitHub URL to a clone URL."""

    parts = repository_parts(url)
    if parts is None:
        return None
    owner, repository = parts
    return f"https://github.com/{owner}/{repository}.git"


class GitHubManager:
    """Clone and update GitHub repositories."""

    def clone_or_pull(
        self,
        url: str,
        destination: Path,
    ) -> None:
        repository = repository_url(url)
        if repository is None:
            raise ValueError(f"Not a GitHub repository URL: {url}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not (destination / ".git").exists():
            raise ValueError(
                f"Repository destination exists but is not a git repository: "
                f"{destination}"
            )

        if (destination / ".git").exists():
            LOGGER.info("Updating repository: %s", repository)
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=destination,
                check=True,
                text=True,
                timeout=600,
            )
            return

        LOGGER.info("Cloning repository: %s", repository)
        subprocess.run(
            ["git", "clone", "--depth", "1", repository, str(destination)],
            check=True,
            text=True,
            timeout=600,
        )
