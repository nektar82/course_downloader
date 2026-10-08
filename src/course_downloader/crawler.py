"""Website crawler."""

from __future__ import annotations

import logging
import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from course_downloader.downloader import Downloader
from course_downloader.github import repository_url
from course_downloader.models import CrawlResult, Source
from course_downloader.utils import normalize_url

LOGGER = logging.getLogger(__name__)

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}
DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".xlsx",
    ".xls",
    ".zip",
    ".csv",
    ".epub",
}


def _matches(pattern: str | None, value: str) -> bool:
    return (
        pattern is not None
        and re.search(pattern, value, re.IGNORECASE) is not None
    )


class CourseCrawler:
    """Crawl public educational sites."""

    def __init__(
        self,
        downloader: Downloader,
        *,
        request_delay_seconds: float = 0.0,
    ) -> None:
        self.downloader = downloader
        self.request_delay_seconds = request_delay_seconds

    def discover(
        self,
        starting_url: str | Source | None = None,
        max_depth: int = 1,
    ) -> CrawlResult:
        source: Source | None = None
        if isinstance(starting_url, Source):
            source = starting_url
            max_depth = source.crawl_depth
            starting_url = source.url

        if not starting_url:
            raise ValueError("A starting URL is required.")

        source = source or Source(
            type="course_page",
            url=starting_url,
            crawl_depth=max_depth,
        )
        return self._discover_for_source(source, starting_url, max_depth)

    def _discover_for_source(
        self,
        source: Source,
        starting_url: str,
        max_depth: int,
    ) -> CrawlResult:
        result = CrawlResult()
        attempted: set[str] = set()
        queue: deque[tuple[str, int]] = deque(
            [(normalize_url(starting_url), 0)]
        )
        start_host = urlparse(starting_url).netloc.lower()
        allowed_domains = {
            domain.lower() for domain in (source.allowed_domains or [])
        }
        allowed_domains.add(start_host)

        while queue:
            if len(attempted) >= source.max_pages:
                result.limit_reached = True
                LOGGER.warning(
                    "Crawler page limit reached for %s", starting_url
                )
                break

            url, depth = queue.popleft()
            if url in attempted:
                continue
            attempted.add(url)

            if len(attempted) > 1 and self.request_delay_seconds:
                time.sleep(self.request_delay_seconds)

            try:
                response = self.downloader.get(url)
            except Exception as exc:
                result.failed_pages.add(url)
                LOGGER.warning("Failed to fetch %s: %s", url, exc)
                continue

            result.pages.add(url)
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type.lower():
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = normalize_url(urljoin(url, str(link["href"])))
                parsed = urlparse(href)
                if parsed.scheme not in {"http", "https"}:
                    continue

                if _matches(source.exclude_regex, href):
                    continue
                if source.include_regex and not _matches(
                    source.include_regex, href
                ):
                    continue

                link_host = parsed.netloc.lower()
                path_suffix = parsed.path.lower()
                is_document = any(
                    path_suffix.endswith(ext) for ext in DOCUMENT_EXTENSIONS
                )

                if link_host in YOUTUBE_HOSTS:
                    if source.discover_youtube:
                        result.youtube.add(href)
                    continue

                repo = repository_url(href)
                if repo:
                    if source.discover_github:
                        result.github.add(repo)
                    continue

                if is_document:
                    if not source.download_documents:
                        continue
                    if (
                        not source.download_external_documents
                        and link_host not in allowed_domains
                    ):
                        continue
                    if source.document_link_regex and not _matches(
                        source.document_link_regex, href
                    ):
                        continue
                    result.documents.add(href)
                    continue

                if link_host not in allowed_domains:
                    continue
                if source.page_include_regex and not _matches(
                    source.page_include_regex, href
                ):
                    continue
                if depth < max_depth:
                    queue.append((href, depth + 1))

        return result
