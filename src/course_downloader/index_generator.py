"""README generation."""

from __future__ import annotations

from pathlib import Path

from course_downloader.models import Course


class IndexGenerator:
    """Generate course indexes."""

    def write_course_readme(
        self,
        course: Course,
        destination: Path,
    ) -> None:

        lines: list[str] = [
            f"# {course.name}",
            "",
        ]

        if course.status:
            lines.extend(
                [
                    f"Status: {course.status}",
                    "",
                ]
            )

        if course.why:
            lines.extend(
                [
                    course.why,
                    "",
                ]
            )

        lines.extend(
            [
                "## Sources",
                "",
            ]
        )

        if course.sources:
            for source in course.sources:
                if source.url:
                    label = source.label or source.type

                    lines.append(f"- {label}: {source.url}")

        destination.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
