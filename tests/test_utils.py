"""Tests for utility functions."""

from course_downloader.utils import (
    format_timestamp,
    normalize_url,
    safe_name,
    slug,
)


def test_safe_name_removes_invalid_characters() -> None:
    assert safe_name("a<b>c:d") == "abcd"


def test_safe_name_empty_returns_default() -> None:
    assert safe_name("") == "untitled"


def test_slug_basic() -> None:
    assert slug("Hello World") == "hello-world"


def test_slug_removes_special_characters() -> None:
    assert slug("Python!!!") == "python"


def test_normalize_url_removes_fragment() -> None:
    result = normalize_url("https://example.com/page#section")

    assert result == "https://example.com/page"


def test_format_timestamp_minutes() -> None:
    assert format_timestamp(125) == "02:05"


def test_format_timestamp_hours() -> None:
    assert format_timestamp(3725) == "01:02:05"
