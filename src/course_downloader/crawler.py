"""Website crawler."""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from course_downloader.downloader import Downloader
from course_downloader.utils import normalize_url

LOGGER = logging.getLogger(__name__)


class CourseCrawler:
    """Crawl public educational sites."""

    def __init__(
        self,
        downloader: Downloader,
    ) -> None:
        self.downloader = downloader

    def discover_pages(
        self,
        starting_url: str,
        max_depth: int = 1,
    ) -> set[str]:
        """Discover crawlable pages."""

        discovered: set[str] = set()

        queue: deque[tuple[str, int]] = deque()

        queue.append(
            (
                normalize_url(starting_url),
                0,
            )
        )

        while queue:
            url, depth = queue.popleft()

            if url in discovered:
                continue

            discovered.add(url)

            if depth >= max_depth:
                continue

            try:
                response = self.downloader.client.get(url)

                response.raise_for_status()

            except Exception as exc:
                LOGGER.warning(
                    "Failed to fetch %s: %s",
                    url,
                    exc,
                )
                continue

            content_type = response.headers.get(
                "content-type",
                "",
            )

            if "html" not in content_type.lower():
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            current_host = urlparse(url).netloc.lower()

            for link in soup.find_all(
                "a",
                href=True,
            ):
                href_value = str(link["href"])

                href = urljoin(
                    url,
                    href_value,
                )

                href = normalize_url(href)

                parsed = urlparse(href)

                if parsed.scheme not in (
                    "http",
                    "https",
                ):
                    continue

                if parsed.netloc.lower() != current_host:
                    continue

                queue.append(
                    (
                        href,
                        depth + 1,
                    )
                )

        return discovered

    def save_page(
        self,
        url: str,
        destination: Path,
    ) -> Path:
        """Download and save a page."""

        return self.downloader.download_file(
            url,
            destination,
        )
