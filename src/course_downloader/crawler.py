"""Website crawler."""

from __future__ import annotations

import logging
import re
from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from course_downloader.downloader import Downloader
from course_downloader.github import repository_url
from course_downloader.models import Source
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


class CourseCrawler:
    """Crawl public educational sites."""

    def __init__(
        self,
        downloader: Downloader,
    ) -> None:
        self.downloader = downloader

    def discover(
        self,
        starting_url: str | Source | None = None,
        max_depth: int = 1,
    ) -> dict[str, set[str]]:
        source: Source | None = None

        if isinstance(starting_url, Source):
            source = starting_url
            max_depth = source.crawl_depth
            starting_url = source.url

        if not starting_url:
            raise ValueError("A starting URL is required.")

        if source is not None:
            return self._discover_for_source(source, starting_url, max_depth)

        return self._discover_for_source(
            Source(
                type="course_page",
                url=starting_url,
                crawl_depth=max_depth,
            ),
            starting_url,
            max_depth,
        )

    def _discover_for_source(
        self,
        source: Source,
        starting_url: str,
        max_depth: int,
    ) -> dict[str, set[str]]:
        discovered_pages: set[str] = set()
        discovered_youtube: set[str] = set()
        discovered_github: set[str] = set()
        discovered_documents: set[str] = set()

        queue: deque[tuple[str, int]] = deque()
        queue.append(
            (
                normalize_url(starting_url),
                0,
            )
        )

        while queue:
            url, depth = queue.popleft()

            if url in discovered_pages:
                continue

            discovered_pages.add(url)

            try:
                response = self.downloader.client.get(
                    url,
                )

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

            host = urlparse(url).netloc.lower()
            allowed_domains = {
                domain.lower() for domain in (source.allowed_domains or [host])
            }

            for link in soup.find_all(
                "a",
                href=True,
            ):
                href = urljoin(
                    url,
                    str(link["href"]),
                )

                href = normalize_url(
                    href,
                )

                parsed = urlparse(
                    href,
                )

                if parsed.scheme not in {
                    "http",
                    "https",
                }:
                    continue

                link_host = parsed.netloc.lower()
                path_suffix = parsed.path.lower()
                is_document = any(
                    path_suffix.endswith(ext) for ext in DOCUMENT_EXTENSIONS
                )

                if source.exclude_regex and re.search(
                    source.exclude_regex,
                    href,
                ):
                    continue

                if source.include_regex and not re.search(
                    source.include_regex,
                    href,
                ):
                    continue

                if link_host in YOUTUBE_HOSTS:
                    if source.discover_youtube:
                        discovered_youtube.add(href)
                    continue

                repo = repository_url(href)
                if repo:
                    if source.discover_github:
                        discovered_github.add(repo)
                    continue

                if is_document:
                    if not source.download_documents:
                        continue
                    if (
                        not source.download_external_documents
                        and link_host not in allowed_domains
                    ):
                        continue
                    if source.document_link_regex and not re.search(
                        source.document_link_regex,
                        href,
                    ):
                        continue
                    discovered_documents.add(href)
                    continue

                if link_host not in allowed_domains:
                    continue

                if source.page_include_regex and not re.search(
                    source.page_include_regex,
                    href,
                ):
                    continue

                if depth < max_depth:
                    queue.append(
                        (
                            href,
                            depth + 1,
                        )
                    )

        return {
            "pages": discovered_pages,
            "youtube": discovered_youtube,
            "github": discovered_github,
            "documents": discovered_documents,
        }
