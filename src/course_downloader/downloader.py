"""HTTP download helpers."""

from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path
from types import TracebackType

import httpx

from course_downloader.constants import (
    DEFAULT_TIMEOUT,
    MAX_DOWNLOAD_SIZE_MB,
    USER_AGENT,
)

LOGGER = logging.getLogger(__name__)


class Downloader:
    """Download public resources safely."""

    def __init__(
        self,
    ) -> None:

        self.client = httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
            },
        )

    def close(
        self,
    ) -> None:
        """Close HTTP resources."""

        self.client.close()

    def download_file(
        self,
        url: str,
        destination: Path,
    ) -> Path:
        """Download a file."""

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_destination = destination.with_suffix(destination.suffix + ".part")
        total_bytes = 0

        try:
            with self.client.stream(
                "GET",
                url,
            ) as response:
                response.raise_for_status()

                content_length = response.headers.get("Content-Length")
                if content_length:
                    size_bytes = int(content_length)
                    if size_bytes / 1024 / 1024 > MAX_DOWNLOAD_SIZE_MB:
                        raise ValueError(
                            "Download exceeds configured size limit."
                        )

                with temp_destination.open("wb") as file:
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue

                        total_bytes += len(chunk)
                        if total_bytes / 1024 / 1024 > MAX_DOWNLOAD_SIZE_MB:
                            raise ValueError(
                                "Download exceeds configured size limit."
                            )

                        file.write(chunk)

            temp_destination.replace(destination)
        except Exception:
            with suppress(FileNotFoundError):
                temp_destination.unlink()
            raise

        LOGGER.info(
            "Downloaded %s",
            url,
        )

        return destination

    def __enter__(
        self,
    ) -> Downloader:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
