"""Source handler behavior tests."""

from pathlib import Path
from unittest.mock import Mock

from course_downloader.course_paths import CoursePaths
from course_downloader.models import Settings, Source
from course_downloader.source_handlers import (
    DocumentProcessor,
    YouTubeSourceHandler,
)
from course_downloader.transcript_fetcher import TranscriptUnavailableError


def test_document_processor_is_incremental(tmp_path: Path) -> None:
    settings = Settings(course_download_root=tmp_path)
    downloader = Mock()
    downloader.download_file.side_effect = lambda _url, destination: (
        destination.write_text("content", encoding="utf-8") or destination
    )
    converter = Mock()
    converter.convert.side_effect = lambda _source, destination: (
        destination.parent.mkdir(parents=True, exist_ok=True)
        or destination.write_text("converted", encoding="utf-8")
        or destination
    )
    paths = CoursePaths(tmp_path, "course")
    paths.create()

    processor = DocumentProcessor(settings, downloader, converter)
    first = processor.process("https://example.com/a.txt", paths)
    destination = next(paths.files.iterdir())
    markdown = paths.markdown / f"{destination.stem}.md"
    assert markdown.exists()
    second = processor.process("https://example.com/a.txt", paths)

    assert first.documents_downloaded == 1
    assert second.documents_skipped == 1


def test_whisper_only_for_unavailable_transcript(tmp_path: Path) -> None:
    settings = Settings(
        course_download_root=tmp_path,
        transcribe_if_no_captions=True,
    )
    client = Mock()
    client.get_entries.return_value = (
        "Playlist",
        [{"id": "abc", "title": "One"}],
    )
    fetcher = Mock()
    fetcher.fetch.side_effect = RuntimeError("temporary API failure")
    paths = CoursePaths(tmp_path, "course")
    paths.create()

    report = YouTubeSourceHandler(settings, client, fetcher).sync(
        Source(type="youtube", url="https://youtube.com/watch?v=abc"),
        paths,
    )
    assert report.transcript_failures == 1
    assert not list(paths.fallback_audio.iterdir())


def test_missing_transcript_is_reported_without_whisper(tmp_path: Path) -> None:
    settings = Settings(
        course_download_root=tmp_path, transcribe_if_no_captions=False
    )
    client = Mock()
    client.get_entries.return_value = (
        "Playlist",
        [{"id": "abc", "title": "One"}],
    )
    fetcher = Mock()
    fetcher.fetch.side_effect = TranscriptUnavailableError("none")
    paths = CoursePaths(tmp_path, "course")
    paths.create()

    report = YouTubeSourceHandler(settings, client, fetcher).sync(
        Source(type="youtube", url="https://youtube.com/watch?v=abc"),
        paths,
    )
    assert report.failed == 1
    assert report.transcript_failures == 1


def test_youtube_success_then_incremental_skip(tmp_path: Path) -> None:
    settings = Settings(course_download_root=tmp_path)
    client = Mock()
    client.get_entries.return_value = (
        "Playlist",
        [{"id": "abc", "title": "One"}],
    )
    fetcher = Mock()
    fetcher.fetch.return_value = [
        {"text": "hello", "start": 0.0, "duration": 1.0}
    ]
    paths = CoursePaths(tmp_path, "course")
    paths.create()
    handler = YouTubeSourceHandler(settings, client, fetcher)

    first = handler.sync(
        Source(type="youtube", url="https://youtube.com/watch?v=abc"),
        paths,
    )
    second = handler.sync(
        Source(type="youtube", url="https://youtube.com/watch?v=abc"),
        paths,
    )

    assert first.transcripts_created == 1
    assert second.transcripts_skipped == 1
    assert fetcher.fetch.call_count == 1


def test_reference_and_github_handlers(tmp_path: Path) -> None:
    from course_downloader.source_handlers import (
        GitHubSourceHandler,
        ReferenceSourceHandler,
    )

    paths = CoursePaths(tmp_path, "course")
    paths.create()
    assert (
        ReferenceSourceHandler()
        .sync(Source(type="reference", url="https://example.com"), paths)
        .skipped
        == 1
    )

    manager = Mock()
    report = GitHubSourceHandler(manager).sync(
        Source(type="github", url="https://github.com/alice/repo"), paths
    )
    assert report.repositories_updated == 1
    destination = manager.clone_or_pull.call_args.args[1]
    assert destination == paths.repos / "alice" / "repo"


def test_course_page_handler_aggregates_nested_work(tmp_path: Path) -> None:
    from course_downloader.models import CrawlResult, SyncReport
    from course_downloader.source_handlers import CoursePageSourceHandler

    settings = Settings(course_download_root=tmp_path)
    crawler = Mock()
    crawler.discover.return_value = CrawlResult(
        pages={"https://example.com"},
        documents={"https://example.com/a.pdf"},
        github={"https://github.com/alice/repo.git"},
        youtube={"https://youtube.com/watch?v=abc"},
    )
    processor = Mock()
    processor.process.return_value = SyncReport(documents_downloaded=1)
    github_handler = Mock()
    github_handler.sync.return_value = SyncReport(repositories_updated=1)
    youtube_handler = Mock()
    youtube_handler.sync.return_value = SyncReport(transcripts_created=1)
    paths = CoursePaths(tmp_path, "course")
    paths.create()

    report = CoursePageSourceHandler(
        settings,
        crawler,
        processor,
        github_handler,
        youtube_handler,
    ).sync(
        Source(type="course_page", url="https://example.com"),
        paths,
    )

    assert report.succeeded == 1
    assert report.pages_fetched == 1
    assert report.documents_downloaded == 1
    assert report.repositories_updated == 1
    assert report.transcripts_created == 1
