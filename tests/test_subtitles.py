"""Subtitle download and parsing tests."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from course_downloader.subtitles import (
    SubtitleDownloader,
    SubtitleError,
    parse_vtt,
)

VTT_SAMPLE = """WEBVTT

00:00:00.000 --> 00:00:02.500
Hello <c>world</c>

00:00:02.500 --> 00:00:04.000
Hello <c>world</c>

00:00:04.000 --> 00:00:06.000
Second cue with <00:00:05.000>inline stamp
"""


def test_parse_vtt_strips_tags_and_dedupes(tmp_path: Path) -> None:
    path = tmp_path / "a.en.vtt"
    path.write_text(VTT_SAMPLE, encoding="utf-8")

    segments = parse_vtt(path)

    assert [segment["text"] for segment in segments] == [
        "Hello world",
        "Second cue with inline stamp",
    ]
    assert segments[0]["start"] == pytest.approx(0.0)
    assert segments[0]["duration"] == pytest.approx(2.5)
    assert segments[1]["start"] == pytest.approx(4.0)


def test_parse_vtt_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.en.vtt"
    path.write_text("WEBVTT\n", encoding="utf-8")
    assert parse_vtt(path) == []


def test_download_prefers_manual_subtitles(tmp_path: Path) -> None:
    downloader = SubtitleDownloader()
    created: list[Path] = []

    def fake_run(command: list[str], **kwargs: object) -> Mock:
        created_path = tmp_path / "abc123.en.vtt"
        if "--write-subs" in command:
            created_path.write_text("WEBVTT\n", encoding="utf-8")
            created.append(created_path)
        return Mock()

    with (
        patch("shutil.which", return_value="/usr/bin/yt-dlp"),
        patch(
            "course_downloader.subtitles.subprocess.run",
            side_effect=fake_run,
        ),
    ):
        path = downloader.download("abc123", ["en"], tmp_path)

    assert path == tmp_path / "abc123.en.vtt"
    assert created == [path]


def test_download_falls_back_to_automatic_captions(tmp_path: Path) -> None:
    downloader = SubtitleDownloader()

    def fake_run(command: list[str], **kwargs: object) -> Mock:
        if "--write-auto-subs" in command:
            (tmp_path / "abc123.en.vtt").write_text(
                "WEBVTT\n", encoding="utf-8"
            )
        return Mock()

    with (
        patch("shutil.which", return_value="/usr/bin/yt-dlp"),
        patch(
            "course_downloader.subtitles.subprocess.run",
            side_effect=fake_run,
        ),
    ):
        path = downloader.download("abc123", ["en"], tmp_path)

    assert path.exists()


def test_download_raises_when_nothing_found(tmp_path: Path) -> None:
    downloader = SubtitleDownloader()
    with (
        patch("shutil.which", return_value="/usr/bin/yt-dlp"),
        patch(
            "course_downloader.subtitles.subprocess.run",
            return_value=Mock(),
        ),
        pytest.raises(SubtitleError),
    ):
        downloader.download("abc123", ["en"], tmp_path)


def test_download_raises_without_yt_dlp(tmp_path: Path) -> None:
    downloader = SubtitleDownloader()
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(SubtitleError),
    ):
        downloader.download("abc123", ["en"], tmp_path)
