"""YouTube integration."""

from __future__ import annotations

import json
import subprocess
from typing import Any


class YouTubeClient:
    """YouTube client."""

    def get_entries(
        self,
        url: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Get playlist or video entries."""

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
        )

        data = json.loads(result.stdout)

        title = data.get("title") or "YouTube"

        entries = data.get("entries") or [data]

        return (
            title,
            entries,
        )
