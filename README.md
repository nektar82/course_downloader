# Course Downloader

Course Downloader builds and maintains a structured local study library from
publicly accessible educational resources. It can crawl public course sites,
download documents, clone public GitHub repositories, collect YouTube
transcripts, convert applicable documents to Markdown, and optionally use local
Whisper transcription when captions are genuinely unavailable.

The application does not bypass authentication, membership requirements,
paywalls, DRM, private content, or course-platform restrictions. Restricted
resources should be represented as `reference` sources.

## Requirements

Required:

- Python 3.14+
- Git
- yt-dlp

Optional for local speech-to-text fallback:

- ffmpeg
- faster-whisper

## Installation

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
```

For development:

```bash
python -m pip install -e .[dev]
```

For Whisper support:

```bash
python -m pip install -e .[whisper]
```

## Running

The installed console entry point is:

```bash
course-downloader --help
```

The package also supports module execution:

```bash
python -m course_downloader --help
```

List courses:

```bash
course-downloader list courses.yaml
```

Validate the manifest:

```bash
course-downloader validate courses.yaml
```

Synchronize all courses:

```bash
course-downloader sync courses.yaml
```

Synchronize one course:

```bash
course-downloader sync courses.yaml --course stanford-cs336-2026
```

The legacy form remains available:

```bash
course-downloader sync-course courses.yaml stanford-cs336-2026
```

Filter by tag, override the course download root, or force reprocessing:

```bash
course-downloader sync courses.yaml --tag iaap
course-downloader sync courses.yaml --course-download-root D:/StudyLibrary
course-downloader sync courses.yaml --course stanford-cs336-2026 --refresh
```

By default, existing downloads and transcripts are reused where possible.
`--refresh` forces document/transcript regeneration. Git repositories are
updated with `git pull --ff-only` on each synchronization.

## Manifest behavior

`course_download_root` is the parent directory that contains all downloaded courses. Each course then has its own `course_root` beneath that directory, derived from the course `path`.

Supported source types are `course_page`, `youtube_playlist`, `youtube_video`,
`youtube`, `github`, `direct`, and `reference`.

The parser rejects unknown keys, invalid regular expressions, negative crawl
depths, malformed URLs, and unsupported source types. Course-page crawling has
a default safety limit of 500 pages per source; override it with `max_pages`
when necessary.

`allowed_domains` controls which HTML pages may be crawled. YouTube and GitHub
links are classified before that restriction. External document downloads are
controlled separately by `download_external_documents`.

Each course writes `metadata/sync-report.json` with the latest synchronization
summary, including document, transcript, repository, page, warning, and failure
counts.

## Reliability model

Downloads are streamed with a maximum-size check, written to `.part` files,
and atomically renamed only after successful completion. Transient HTTP errors
are retried with bounded exponential backoff and `Retry-After` support.

A missing YouTube transcript can trigger Whisper only when
`transcribe_if_no_captions` is enabled. Transient transcript-service failures
do not automatically trigger an expensive audio download and transcription.

## Development

```bash
ruff format .
ruff check . --fix
mypy src
pytest
```

CI runs formatting, linting, strict type checking, tests, coverage, and CLI
smoke tests on Linux and Windows.

## Security

Manifests are trusted configuration. Review manifests from other people before
running them. Downloaded repositories are not executed by Course Downloader.
See `SECURITY.md` for the project's security boundary.

## License

MIT. See `LICENSE`.
