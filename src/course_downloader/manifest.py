"""Manifest parsing and semantic validation."""

from __future__ import annotations

import re
from typing import Any, cast
from urllib.parse import urlparse

from course_downloader.constants import DEFAULT_MAX_PAGES
from course_downloader.models import Course, Source, SourceType

VALID_SOURCE_TYPES: set[str] = {
    "youtube",
    "youtube_playlist",
    "youtube_video",
    "github",
    "direct",
    "course_page",
    "reference",
}
_ALLOWED_COURSE_KEYS = {
    "id",
    "name",
    "path",
    "status",
    "why",
    "tags",
    "sources",
}
_ALLOWED_SOURCE_KEYS = {
    "type",
    "url",
    "label",
    "crawl_depth",
    "max_pages",
    "download_documents",
    "download_external_documents",
    "discover_youtube",
    "discover_github",
    "allowed_domains",
    "include_regex",
    "exclude_regex",
    "page_include_regex",
    "document_link_regex",
}
_BOOL_SOURCE_KEYS = {
    "download_documents",
    "download_external_documents",
    "discover_youtube",
    "discover_github",
}
_REGEX_SOURCE_KEYS = {
    "include_regex",
    "exclude_regex",
    "page_include_regex",
    "document_link_regex",
}


def _require_non_empty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a non-empty string.")
    return value


def _validate_url(value: Any, where: str) -> str:
    url = _require_non_empty_string(value, where)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{where} must be an http(s) URL.")
    return url


def _reject_unknown_keys(
    item: dict[str, Any],
    allowed: set[str],
    where: str,
) -> None:
    unknown = sorted(set(item) - allowed)
    if unknown:
        raise ValueError(f"Unknown key(s) in {where}: {', '.join(unknown)}")


def parse_sources(
    data: list[dict[str, Any]],
    *,
    course_id: str = "<unknown>",
) -> list[Source]:
    """Parse and validate source definitions."""

    if not isinstance(data, list):
        raise ValueError(f"courses[{course_id}].sources must be a list.")

    parsed: list[Source] = []
    for index, item in enumerate(data):
        where = f"courses[{course_id}].sources[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be a mapping.")
        _reject_unknown_keys(item, _ALLOWED_SOURCE_KEYS, where)

        source_type = _require_non_empty_string(
            item.get("type"), f"{where}.type"
        )
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source type at {where}: {source_type!r}. "
                f"Expected one of {sorted(VALID_SOURCE_TYPES)}."
            )

        url = _validate_url(item.get("url"), f"{where}.url")
        crawl_depth = item.get("crawl_depth", 1)
        max_pages = item.get("max_pages", DEFAULT_MAX_PAGES)
        if not isinstance(crawl_depth, int) or isinstance(crawl_depth, bool):
            raise ValueError(f"{where}.crawl_depth must be an integer.")
        if crawl_depth < 0:
            raise ValueError(f"{where}.crawl_depth cannot be negative.")
        if not isinstance(max_pages, int) or isinstance(max_pages, bool):
            raise ValueError(f"{where}.max_pages must be an integer.")
        if max_pages <= 0:
            raise ValueError(f"{where}.max_pages must be greater than zero.")

        for key in _BOOL_SOURCE_KEYS:
            if key in item and not isinstance(item[key], bool):
                raise ValueError(f"{where}.{key} must be a boolean.")

        allowed_domains = item.get("allowed_domains")
        if allowed_domains is not None and (
            not isinstance(allowed_domains, list)
            or not all(
                isinstance(domain, str) and domain for domain in allowed_domains
            )
        ):
            raise ValueError(
                f"{where}.allowed_domains must be a list of strings."
            )

        for key in _REGEX_SOURCE_KEYS:
            pattern = item.get(key)
            if pattern is not None:
                if not isinstance(pattern, str):
                    raise ValueError(f"{where}.{key} must be a string.")
                try:
                    re.compile(pattern, re.IGNORECASE)
                except re.error as exc:
                    raise ValueError(
                        f"Invalid regex in {where}.{key}: {exc}"
                    ) from exc

        parsed.append(
            Source(
                type=cast(SourceType, source_type),
                url=url,
                label=item.get("label"),
                crawl_depth=crawl_depth,
                max_pages=max_pages,
                download_documents=item.get("download_documents", True),
                download_external_documents=item.get(
                    "download_external_documents", True
                ),
                discover_youtube=item.get("discover_youtube", True),
                discover_github=item.get("discover_github", True),
                allowed_domains=allowed_domains,
                include_regex=item.get("include_regex"),
                exclude_regex=item.get("exclude_regex"),
                page_include_regex=item.get("page_include_regex"),
                document_link_regex=item.get("document_link_regex"),
            )
        )

    return parsed


def parse_courses(manifest: dict[str, Any]) -> list[Course]:
    """Parse and validate course definitions."""

    courses: list[Course] = []
    for index, item in enumerate(manifest["courses"]):
        where = f"courses[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be a mapping.")
        _reject_unknown_keys(item, _ALLOWED_COURSE_KEYS, where)

        course_id = _require_non_empty_string(item.get("id"), f"{where}.id")
        name = _require_non_empty_string(item.get("name"), f"{where}.name")
        path = _require_non_empty_string(item.get("path"), f"{where}.path")
        tags = item.get("tags")
        if tags is not None and (
            not isinstance(tags, list)
            or not all(isinstance(tag, str) and tag for tag in tags)
        ):
            raise ValueError(f"{where}.tags must be a list of strings.")

        courses.append(
            Course(
                id=course_id,
                name=name,
                path=path,
                status=item.get("status"),
                why=item.get("why"),
                tags=tags,
                sources=parse_sources(
                    item.get("sources", []), course_id=course_id
                ),
            )
        )

    return courses
