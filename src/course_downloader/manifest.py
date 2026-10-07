"""Manifest parsing."""

from __future__ import annotations

from typing import Any

from course_downloader.models import Course, Source

VALID_SOURCE_TYPES = {
    "youtube",
    "youtube_playlist",
    "youtube_video",
    "github",
    "direct",
    "course_page",
    "reference",
}


def parse_sources(
    data: list[dict[str, Any]],
) -> list[Source]:
    """Parse source definitions."""

    parsed: list[Source] = []

    for item in data:
        source_type = item["type"]
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source type: {source_type!r}. "
                f"Expected one of {sorted(VALID_SOURCE_TYPES)}."
            )

        parsed.append(
            Source(
                type=source_type,
                url=item.get("url"),
                label=item.get("label"),
                crawl_depth=item.get("crawl_depth", 1),
                download_documents=item.get("download_documents", True),
                download_external_documents=item.get(
                    "download_external_documents",
                    True,
                ),
                discover_youtube=item.get("discover_youtube", True),
                discover_github=item.get("discover_github", True),
                allowed_domains=item.get("allowed_domains"),
                include_regex=item.get("include_regex"),
                exclude_regex=item.get("exclude_regex"),
                page_include_regex=item.get("page_include_regex"),
                document_link_regex=item.get("document_link_regex"),
            )
        )

    return parsed


def parse_courses(
    manifest: dict[str, Any],
) -> list[Course]:
    """Parse course definitions."""

    courses: list[Course] = []

    for item in manifest["courses"]:
        courses.append(
            Course(
                id=item["id"],
                name=item["name"],
                path=item["path"],
                status=item.get("status"),
                why=item.get("why"),
                tags=item.get("tags"),
                sources=parse_sources(
                    item.get(
                        "sources",
                        [],
                    )
                ),
            )
        )

    return courses
