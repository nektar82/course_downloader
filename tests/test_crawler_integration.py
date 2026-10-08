"""Crawler pipeline tests."""

from unittest.mock import Mock

from course_downloader.crawler import CourseCrawler


def test_discovery_pipeline() -> None:
    downloader = Mock()
    response = Mock()
    response.headers = {"content-type": "text/html"}
    response.text = """
    <html><body>
      <a href="https://youtube.com/watch?v=test">Video</a>
      <a href="https://github.com/user/repo">Repo</a>
      <a href="slides.pdf">Slides</a>
    </body></html>
    """
    downloader.get.return_value = response

    discovered = CourseCrawler(downloader).discover("https://example.com")
    assert len(discovered.youtube) == 1
    assert len(discovered.github) == 1
    assert len(discovered.documents) == 1
