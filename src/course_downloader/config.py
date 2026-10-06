"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from course_downloader.models import Settings

Manifest = dict[str, Any]


def load_manifest(path: Path) -> Manifest:
    """Load and validate the course manifest.

    Args:
        path: Path to the YAML manifest.

    Returns:
        Parsed manifest dictionary.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If the manifest structure is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest file does not exist: {path}")

    with path.open(
        mode="r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Manifest must contain a mapping.")

    courses = data.get("courses")

    if not isinstance(courses, list):
        raise ValueError("Manifest must contain a 'courses' list.")

    return data


def build_settings(
    manifest: Manifest,
) -> Settings:
    """Build application settings.

    Args:
        manifest: Loaded manifest.

    Returns:
        Application settings.
    """
    defaults = manifest.get(
        "defaults",
        {},
    )

    root = Path(
        manifest.get(
            "library_root",
            "CourseLibrary",
        )
    ).expanduser()

    return Settings(
        root=root,
        timestamp_minutes=int(
            defaults.get(
                "timestamp_minutes",
                5,
            )
        ),
        paragraph_chars=int(
            defaults.get(
                "paragraph_chars",
                700,
            )
        ),
        languages=tuple(
            defaults.get(
                "languages",
                [
                    "en",
                    "en-US",
                    "en-GB",
                ],
            )
        ),
        transcribe_if_no_captions=bool(
            defaults.get(
                "transcribe_if_no_captions",
                False,
            )
        ),
        whisper_model=str(
            defaults.get(
                "whisper_model",
                "small",
            )
        ),
        keep_fallback_audio=bool(
            defaults.get(
                "keep_fallback_audio",
                False,
            )
        ),
        request_delay_seconds=float(
            defaults.get(
                "request_delay_seconds",
                0.15,
            )
        ),
        timeout_seconds=int(
            defaults.get(
                "timeout",
                45,
            )
        ),
    )
