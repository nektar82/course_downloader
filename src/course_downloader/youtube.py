"""YouTube integration."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlparse

LOGGER = logging.getLogger(__name__)

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _single_video_id(url: str) -> str | None:
    """Extract a video ID from a single-video URL, if it is one."""

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtube.com" not in host and "youtu.be" not in host:
        return None
    if "youtube.com" in host:
        query = parse_qs(parsed.query)
        if "list" in query:
            return None
        candidates = query.get("v", [])
    else:
        candidates = [parsed.path.strip("/").split("/")[0]]
    for candidate in candidates:
        if _VIDEO_ID_RE.match(candidate):
            return candidate
    return None


class YouTubeClient:
    """YouTube client."""

    def get_entries(
        self,
        url: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Get playlist or video entries."""

        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--flat-playlist",
                    "--dump-single-json",
                    url,
                ],
                check=True,
                text=True,
                capture_output=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            video_id = _single_video_id(url)
            if video_id is None:
                raise
            # Include yt-dlp's stderr so we know WHY it failed
            # (bot detection, video removed, no captions, etc.)
            raw_stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            stderr_lines = raw_stderr.strip().splitlines()
            reason = (
                stderr_lines[-1].strip()
                if stderr_lines
                else f"exit {exc.returncode}"
            )
            LOGGER.warning(
                "yt-dlp could not read %s: %s; treating it as a single "
                "video so subtitles can still be attempted.",
                url,
                reason,
            )
            return (
                "YouTube",
                [{"id": video_id, "title": f"Video {video_id}"}],
            )

        data = json.loads(result.stdout)

        title = data.get("title") or "YouTube"

        entries = data.get("entries")

        if entries:
            return (
                title,
                entries,
            )

        return (
            title,
            [data],
        )
