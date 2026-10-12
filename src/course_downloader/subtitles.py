"""YouTube subtitle download and parsing fallback.

The transcript API is blocked from some networks (YouTube returns
``IpBlocked`` for datacenter egress IPs). Downloading the subtitle file
with yt-dlp is a cheap alternative that avoids the expensive Whisper audio
pipeline, so it is attempted before Whisper.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})"
    r"\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})"
)
_TAG_RE = re.compile(r"<[^>]+>")
_BLANK_LINE_RE = re.compile(r"\r?\n\r?\n")


class SubtitleError(RuntimeError):
    """Raised when subtitles cannot be downloaded or parsed."""


def _timestamp_to_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def parse_vtt(path: Path) -> list[dict[str, Any]]:
    """Parse a WebVTT file into transcript segments."""

    text = path.read_text(encoding="utf-8", errors="replace")
    segments: list[dict[str, Any]] = []
    previous_text = ""
    for block in _BLANK_LINE_RE.split(text):
        lines = [
            line.strip() for line in block.strip().splitlines() if line.strip()
        ]
        if not lines:
            continue
        match = None
        cue_lines: list[str] = []
        for line in lines:
            found = _TIMESTAMP_RE.search(line)
            if found is not None and match is None:
                match = found
            elif match is not None:
                cue_lines.append(line)
        if match is None:
            continue
        cue_text = _TAG_RE.sub("", " ".join(cue_lines))
        cue_text = re.sub(r"\s+", " ", cue_text).strip()
        if not cue_text or cue_text == previous_text:
            continue
        previous_text = cue_text
        start = _timestamp_to_seconds(match.group("start"))
        end = _timestamp_to_seconds(match.group("end"))
        segments.append(
            {
                "text": cue_text,
                "start": start,
                "duration": max(0.0, end - start),
            }
        )
    return segments


class SubtitleDownloader:
    """Download YouTube subtitle files with yt-dlp."""

    def __init__(self, *, timeout_seconds: int = 300) -> None:
        self.timeout_seconds = timeout_seconds

    def download(
        self,
        video_id: str,
        languages: list[str],
        destination_dir: Path,
    ) -> Path:
        """Download the best available subtitle file for a video.

        Prefers manually created subtitles over automatic captions, and
        retries with the Android player client when the default web client
        is bot-blocked. Returns the downloaded ``.vtt`` path.
        """

        if shutil.which("yt-dlp") is None:
            raise SubtitleError("yt-dlp is not installed.")

        destination_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://www.youtube.com/watch?v={video_id}"
        for automatic in (False, True):
            for player_client in (None, "android"):
                path = self._attempt(
                    url,
                    video_id,
                    languages,
                    destination_dir,
                    automatic=automatic,
                    player_client=player_client,
                )
                if path is not None:
                    kind = "automatic" if automatic else "manual"
                    LOGGER.info(
                        "Downloaded %s subtitles for %s", kind, video_id
                    )
                    return path
        raise SubtitleError(f"No subtitles available for {video_id}.")

    def _attempt(
        self,
        url: str,
        video_id: str,
        languages: list[str],
        destination_dir: Path,
        *,
        automatic: bool,
        player_client: str | None,
    ) -> Path | None:
        for stale in destination_dir.glob(f"{video_id}.*.vtt"):
            stale.unlink()
        command = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs" if automatic else "--write-subs",
            "--sub-langs",
            ",".join(languages),
            "--sub-format",
            "vtt",
            "--no-playlist",
            "-o",
            str(destination_dir / f"{video_id}.%(ext)s"),
        ]
        if player_client is not None:
            command += [
                "--extractor-args",
                f"youtube:player_client={player_client}",
            ]
        command.append(url)
        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            LOGGER.warning("Subtitle download failed for %s: %s", url, exc)
            return None
        candidates = sorted(destination_dir.glob(f"{video_id}.*.vtt"))
        return candidates[0] if candidates else None
