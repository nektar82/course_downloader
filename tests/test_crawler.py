"""Crawler tests."""

from unittest.mock import Mock

from course_downloader.crawler import CourseCrawler
from course_downloader.models import Source


def _downloader_with_html(html: str) -> Mock:
    downloader = Mock()
    response = Mock()
    response.headers = {"content-type": "text/html"}
    response.text = html
    downloader.get.return_value = response
    return downloader


def test_discover_single_page() -> None:
    downloader = _downloader_with_html("<html><body></body></html>")
    discovered = CourseCrawler(downloader).discover("https://example.com")
    assert "https://example.com" in discovered.pages


def test_discover_youtube_and_github() -> None:
    downloader = _downloader_with_html(
        """
        <a href="https://youtube.com/watch?v=test">Video</a>
        <a href="https://github.com/user/repo">Repo</a>
        """
    )
    discovered = CourseCrawler(downloader).discover("https://example.com")
    assert len(discovered.youtube) == 1
    assert len(discovered.github) == 1


def test_discover_document_at_depth_zero() -> None:
    downloader = _downloader_with_html('<a href="slides.pdf">Slides</a>')
    source = Source(
        type="course_page",
        url="https://example.com",
        crawl_depth=0,
    )
    discovered = CourseCrawler(downloader).discover(source)
    assert discovered.documents == {"https://example.com/slides.pdf"}


def test_external_document_can_be_blocked() -> None:
    downloader = _downloader_with_html(
        '<a href="https://cdn.example.net/slides.pdf">Slides</a>'
    )
    source = Source(
        type="course_page",
        url="https://example.com",
        download_external_documents=False,
    )
    discovered = CourseCrawler(downloader).discover(source)
    assert not discovered.documents


def test_page_regex_does_not_filter_documents() -> None:
    downloader = _downloader_with_html(
        '<a href="slides.pdf">Slides</a><a href="other.html">Other</a>'
    )
    source = Source(
        type="course_page",
        url="https://example.com",
        page_include_regex="week",
    )
    discovered = CourseCrawler(downloader).discover(source)
    assert discovered.documents == {"https://example.com/slides.pdf"}


def test_max_pages_stops_crawl() -> None:
    downloader = _downloader_with_html('<a href="one.html">One</a>')
    source = Source(
        type="course_page",
        url="https://example.com",
        crawl_depth=5,
        max_pages=1,
    )
    discovered = CourseCrawler(downloader).discover(source)
    assert discovered.limit_reached is True
    assert len(discovered.pages) == 1
