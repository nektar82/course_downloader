"""Crawler tests."""

from unittest.mock import Mock

from course_downloader.crawler import (
    CourseCrawler,
)
from course_downloader.downloader import (
    Downloader,
)


def test_crawler_creation() -> None:

    downloader = Mock(spec=Downloader)

    crawler = CourseCrawler(downloader)

    assert crawler is not None
