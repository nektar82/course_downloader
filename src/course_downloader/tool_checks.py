"""External tool verification."""

from __future__ import annotations

import shutil


class ToolCheck:
    """Result of a tool check."""

    def __init__(
        self,
        name: str,
        installed: bool,
        required: bool,
    ) -> None:
        self.name = name
        self.installed = installed
        self.required = required


def check_tools() -> list[ToolCheck]:
    """Check external dependencies."""

    return [
        ToolCheck(
            name="git",
            installed=(shutil.which("git") is not None),
            required=True,
        ),
        ToolCheck(
            name="yt-dlp",
            installed=(shutil.which("yt-dlp") is not None),
            required=True,
        ),
        ToolCheck(
            name="ffmpeg",
            installed=(shutil.which("ffmpeg") is not None),
            required=False,
        ),
    ]
