"""Course directory management."""

from __future__ import annotations

from pathlib import Path


class CoursePaths:
    """Course output paths."""

    def __init__(
        self,
        root: Path,
        course_path: str,
    ) -> None:

        self.base = root / Path(course_path)

        self.lectures = self.base / "lectures"

        self.raw_transcripts = self.base / "raw" / "transcripts"

        self.fallback_audio = self.base / "raw" / "audio"

        self.web = self.base / "source" / "web"

        self.files = self.base / "source" / "files"

        self.repos = self.base / "source" / "repos"

        self.markdown = self.base / "markdown"

        self.metadata = self.base / "metadata"

        self.logs = self.base / "logs"

    def create(
        self,
    ) -> None:

        for path in (
            self.base,
            self.lectures,
            self.raw_transcripts,
            self.fallback_audio,
            self.web,
            self.files,
            self.repos,
            self.markdown,
            self.metadata,
            self.logs,
        ):
            path.mkdir(
                parents=True,
                exist_ok=True,
            )
