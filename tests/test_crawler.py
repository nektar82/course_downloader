"""Crawler tests."""

from unittest.mock import Mock

from course_downloader.crawler import (
    CourseCrawler,
)


def test_crawler_creation() -> None:
    downloader = Mock()
    downloader.client = Mock()

    crawler = CourseCrawler(
        downloader,
    )

    assert crawler is not None


def test_discover_single_page() -> None:
    downloader = Mock()
    downloader.client = Mock()

    response = Mock()

    response.headers = {
        "content-type": "text/html",
    }

    response.text = """
    <html>
      <body></body>
    </html>
    """

    response.raise_for_status = Mock()

    downloader.client.get.return_value = response

    crawler = CourseCrawler(
        downloader,
    )

    discovered = crawler.discover(
        "https://example.com",
    )

    assert "https://example.com" in discovered["pages"]


def test_discover_youtube() -> None:
    downloader = Mock()
    downloader.client = Mock()

    response = Mock()

    response.headers = {
        "content-type": "text/html",
    }

    response.text = """
    <html>
      <body>
        <a href="https://youtube.com/watch?v=test">
          Video
        </a>
      </body>
    </html>
    """

    response.raise_for_status = Mock()

    downloader.client.get.return_value = response

    crawler = CourseCrawler(
        downloader,
    )

    discovered = crawler.discover(
        "https://example.com",
    )

    assert len(discovered["youtube"]) == 1


def test_discover_github() -> None:
    downloader = Mock()
    downloader.client = Mock()

    response = Mock()

    response.headers = {
        "content-type": "text/html",
    }

    response.text = """
    <html>
      <body>
        <a href="https://github.com/user/repo">
          Repo
        </a>
      </body>
    </html>
    """

    response.raise_for_status = Mock()

    downloader.client.get.return_value = response

    crawler = CourseCrawler(
        downloader,
    )

    discovered = crawler.discover(
        "https://example.com",
    )

    assert len(discovered["github"]) == 1


def test_discover_document() -> None:
    downloader = Mock()
    downloader.client = Mock()

    response = Mock()

    response.headers = {
        "content-type": "text/html",
    }

    response.text = """
    <html>
      <body>
        <a href="slides.pdf">
          Slides
        </a>
      </body>
    </html>
    """

    response.raise_for_status = Mock()

    downloader.client.get.return_value = response

    crawler = CourseCrawler(
        downloader,
    )

    discovered = crawler.discover(
        "https://example.com",
    )

    assert len(discovered["documents"]) == 1
