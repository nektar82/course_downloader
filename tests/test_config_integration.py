"""Config integration."""

from pathlib import Path

from course_downloader.config import (
    build_settings,
    load_manifest,
)


def test_manifest_to_settings(
    tmp_path: Path,
) -> None:
    manifest_file = tmp_path / "manifest.yml"

    manifest_file.write_text(
        """
library_root: TestLibrary

defaults:
  timestamp_minutes: 15
  paragraph_chars: 500

courses:
  - id: course
    name: Course
    path: course
""",
        encoding="utf-8",
    )

    manifest = load_manifest(
        manifest_file,
    )

    settings = build_settings(
        manifest,
    )

    assert settings.root.name == "TestLibrary"

    assert settings.timestamp_minutes == 15

    assert settings.paragraph_chars == 500
