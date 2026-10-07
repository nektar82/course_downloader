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
        self.root = root.resolve()
        requested = (self.root / Path(course_path)).resolve()

        try:
            requested.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                f"Course path escapes library root: {course_path}"
            ) from exc

        self.course_root = requested

        self.lectures = self.course_root / "lectures"

        self.raw_transcripts = self.course_root / "raw" / "transcripts"

        self.fallback_audio = self.course_root / "raw" / "audio"

        self.web = self.course_root / "source" / "web"

        self.files = self.course_root / "source" / "files"

        self.repos = self.course_root / "source" / "repos"

        self.markdown = self.course_root / "markdown"

        self.metadata = self.course_root / "metadata"

        self.logs = self.course_root / "logs"

    def create(
        self,
    ) -> None:

        for path in (
            self.course_root,
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
