"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from course_downloader.models import Settings

Manifest = dict[str, Any]

_ALLOWED_TOP_LEVEL = {"course_download_root", "defaults", "courses"}
_ALLOWED_DEFAULTS = {
    "timestamp_minutes",
    "paragraph_chars",
    "languages",
    "transcribe_if_no_captions",
    "whisper_model",
    "keep_fallback_audio",
    "request_delay_seconds",
    "timeout",
}


def _unknown_keys(data: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"Unknown key(s) in {where}: {', '.join(unknown)}")


def load_manifest(path: Path) -> Manifest:
    """Load and perform top-level validation of a YAML manifest."""

    if not path.exists():
        raise FileNotFoundError(f"Manifest file does not exist: {path}")

    with path.open(mode="r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Manifest must contain a mapping.")

    _unknown_keys(data, _ALLOWED_TOP_LEVEL, "manifest")

    courses = data.get("courses")
    if not isinstance(courses, list):
        raise ValueError("Manifest must contain a 'courses' list.")

    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("Manifest 'defaults' must be a mapping.")
    _unknown_keys(defaults, _ALLOWED_DEFAULTS, "defaults")

    return data


def build_settings(
    manifest: Manifest,
    *,
    course_download_root_override: Path | None = None,
    refresh: bool = False,
) -> Settings:
    """Build validated application settings."""

    defaults = manifest.get("defaults", {})
    configured_course_download_root = str(
        manifest.get("course_download_root") or "CourseLibrary"
    )
    course_download_root = (
        course_download_root_override or Path(configured_course_download_root)
    ).expanduser()

    timestamp_minutes = int(defaults.get("timestamp_minutes", 5))
    paragraph_chars = int(defaults.get("paragraph_chars", 700))
    request_delay_seconds = float(defaults.get("request_delay_seconds", 0.15))
    timeout_seconds = int(defaults.get("timeout", 45))
    languages_raw = defaults.get("languages", ["en", "en-US", "en-GB"])
    for key in ("transcribe_if_no_captions", "keep_fallback_audio"):
        if key in defaults and not isinstance(defaults[key], bool):
            raise ValueError(f"defaults.{key} must be a boolean.")

    if timestamp_minutes <= 0:
        raise ValueError(
            "defaults.timestamp_minutes must be greater than zero."
        )
    if paragraph_chars <= 0:
        raise ValueError("defaults.paragraph_chars must be greater than zero.")
    if request_delay_seconds < 0:
        raise ValueError("defaults.request_delay_seconds cannot be negative.")
    if timeout_seconds <= 0:
        raise ValueError("defaults.timeout must be greater than zero.")
    if not isinstance(languages_raw, list) or not all(
        isinstance(item, str) and item for item in languages_raw
    ):
        raise ValueError(
            "defaults.languages must be a non-empty list of strings."
        )

    return Settings(
        course_download_root=course_download_root,
        timestamp_minutes=timestamp_minutes,
        paragraph_chars=paragraph_chars,
        languages=tuple(languages_raw),
        transcribe_if_no_captions=bool(
            defaults.get("transcribe_if_no_captions", False)
        ),
        whisper_model=str(defaults.get("whisper_model", "small")),
        keep_fallback_audio=bool(defaults.get("keep_fallback_audio", False)),
        request_delay_seconds=request_delay_seconds,
        timeout_seconds=timeout_seconds,
        refresh=refresh,
    )
