"""HTTP download helpers."""

from __future__ import annotations

import logging
import time
from contextlib import suppress
from pathlib import Path
from types import TracebackType

import httpx

from course_downloader.constants import (
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_DEADLINE,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    MAX_DOWNLOAD_SIZE_MB,
    RETRY_STATUS_CODES,
    USER_AGENT,
)

LOGGER = logging.getLogger(__name__)


class Downloader:
    """Download public resources with bounded retries and atomic writes."""

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT,
        deadline_seconds: float = DEFAULT_DEADLINE,
        max_size_mb: int = MAX_DOWNLOAD_SIZE_MB,
        retries: int = DEFAULT_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ) -> None:
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.deadline_seconds = deadline_seconds
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    def close(self) -> None:
        """Close HTTP resources."""

        self.client.close()

    def _delay(
        self, attempt: int, response: httpx.Response | None = None
    ) -> None:
        retry_after = (
            None if response is None else response.headers.get("Retry-After")
        )
        if retry_after is not None:
            with suppress(ValueError):
                time.sleep(max(0.0, float(retry_after)))
                return
        time.sleep(self.backoff_seconds * (2**attempt))

    def _check_deadline(self, start: float, url: str) -> None:
        """Raise TimeoutException if the overall operation deadline elapsed.

        httpx timeouts are per-read operation: a server that keeps trickling
        data (even very slowly) never triggers them, so without this a single
        stalled transfer can hang the sync indefinitely with no log output.
        """

        if time.monotonic() - start > self.deadline_seconds:
            raise httpx.TimeoutException(
                f"overall deadline of {self.deadline_seconds}s exceeded "
                f"for {url}",
            )

    def get(self, url: str) -> httpx.Response:
        """GET a URL with retries for transient transport/server failures.

        Streams the response with an overall deadline so a slow-trickling
        server cannot hang the call forever; callers see a normal
        httpx.Response either way.
        """

        for attempt in range(self.retries + 1):
            start = time.monotonic()
            try:
                with self.client.stream("GET", url) as response:
                    if (
                        response.status_code in RETRY_STATUS_CODES
                        and attempt < self.retries
                    ):
                        self._delay(attempt, response)
                        continue
                    response.raise_for_status()
                    chunks: list[bytes] = []
                    for chunk in response.iter_bytes():
                        self._check_deadline(start, url)
                        chunks.append(chunk)
                return httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=b"".join(chunks),
                    request=response.request,
                )
            except httpx.DecodingError:
                # Some servers send a Content-Encoding their body does not
                # actually match (e.g. "deflate" with a raw stream), and zlib
                # fails with "Error -3: incorrect header check". Retry once
                # asking for an uncompressed body instead of giving up; this
                # was silently failing whole courses (IAAP, pwn.college, OST2).
                if getattr(self, "_identity_retry", None) == url:
                    raise
                self._identity_retry = url
                LOGGER.warning(
                    "Decompression failed for %s; retrying uncompressed", url
                )
                with self.client.stream(
                    "GET", url, headers={"Accept-Encoding": "identity"}
                ) as response:
                    response.raise_for_status()
                    chunks = []
                    for chunk in response.iter_raw():
                        self._check_deadline(start, url)
                        chunks.append(chunk)
                return httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=b"".join(chunks),
                    request=response.request,
                )
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt >= self.retries:
                    raise
                self._delay(attempt)

        raise RuntimeError("HTTP retry loop exhausted unexpectedly.")

    def download_file(self, url: str, destination: Path) -> Path:
        """Download a file atomically while enforcing a streaming size limit."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_destination = destination.with_suffix(destination.suffix + ".part")

        for attempt in range(self.retries + 1):
            total_bytes = 0
            start = time.monotonic()
            try:
                with self.client.stream("GET", url) as response:
                    status_code = response.status_code
                    if (
                        status_code in RETRY_STATUS_CODES
                        and attempt < self.retries
                    ):
                        self._delay(attempt, response)
                        continue

                    response.raise_for_status()
                    content_length = response.headers.get("Content-Length")
                    if (
                        content_length
                        and int(content_length) > self.max_size_bytes
                    ):
                        raise ValueError(
                            "Download exceeds configured size limit."
                        )

                    with temp_destination.open("wb") as file:
                        for chunk in response.iter_bytes():
                            self._check_deadline(start, url)
                            if not chunk:
                                continue
                            total_bytes += len(chunk)
                            if total_bytes > self.max_size_bytes:
                                raise ValueError(
                                    "Download exceeds configured size limit."
                                )
                            file.write(chunk)

                temp_destination.replace(destination)
                LOGGER.info("Downloaded %s", url)
                return destination
            except (httpx.TimeoutException, httpx.TransportError):
                with suppress(FileNotFoundError):
                    temp_destination.unlink()
                if attempt >= self.retries:
                    raise
                self._delay(attempt)
            except Exception:
                with suppress(FileNotFoundError):
                    temp_destination.unlink()
                raise

        raise RuntimeError("HTTP retry loop exhausted unexpectedly.")

    def __enter__(self) -> Downloader:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
