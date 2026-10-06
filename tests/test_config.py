"""Tests for configuration loading."""

from pathlib import Path

import pytest

from course_downloader.config import load_manifest


def test_load_manifest(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "courses.yaml"

    manifest.write_text(
        """
courses:
  - id: sample
        """,
        encoding="utf-8",
    )

    data = load_manifest(manifest)

    assert "courses" in data


def test_invalid_manifest(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "courses.yaml"

    manifest.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_manifest(manifest)
