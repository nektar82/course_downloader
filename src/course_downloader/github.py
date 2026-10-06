"""GitHub integration."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)

GITHUB_RE = re.compile(
    r"^https?://github\.com/"
    r"([^/]+)/"
    r"([^/#?]+)",
    re.IGNORECASE,
)


def repository_url(
    url: str,
) -> str | None:
    """Convert a GitHub URL to a clone URL."""

    match = GITHUB_RE.match(url)

    if not match:
        return None

    owner = match.group(1)

    repository = match.group(2).removesuffix(".git")

    return f"https://github.com/{owner}/{repository}.git"


class GitHubManager:
    """Clone and update repositories."""

    def clone_or_pull(
        self,
        url: str,
        destination: Path,
    ) -> None:

        repository = repository_url(url) or url

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists() and (destination / ".git").exists():
            LOGGER.info(
                "Updating repository: %s",
                repository,
            )

            subprocess.run(
                [
                    "git",
                    "pull",
                    "--ff-only",
                ],
                cwd=destination,
                check=True,
                text=True,
            )

            return

        LOGGER.info(
            "Cloning repository: %s",
            repository,
        )

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repository,
                str(destination),
            ],
            check=True,
            text=True,
        )
