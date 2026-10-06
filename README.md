# Course Downloader

Course Downloader is a Python application for building and maintaining a structured local study library from publicly accessible educational resources.

The project can:

- Crawl public course websites
- Discover and download public course documents
- Clone public GitHub repositories
- Collect YouTube transcripts
- Convert downloaded resources to Markdown
- Generate per-course indexes
- Optionally perform local Whisper transcription for videos that do not have public captions

The software is intentionally designed to respect access controls.

It does not attempt to bypass:

- Authentication
- Membership requirements
- Paywalls
- DRM
- Private content
- Course platform restrictions

Restricted resources are stored only as references.

---

# Features

Supported source types:

| Type | Description |
|--------|-------------|
| course_page | Crawl public course websites |
| youtube_playlist | Process YouTube playlists |
| youtube_video | Process single YouTube videos |
| github | Clone or update GitHub repositories |
| direct | Download explicit public files |
| reference | Store URLs without downloading |

---

# Installation

## Requirements

Required:

- Python 3.13+
- Git
- yt-dlp

Optional:

- ffmpeg
- faster-whisper

---

## Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install

```bash
pip install -e .
```

Development installation:

```bash
pip install -e .[dev]
```

Whisper support:

```bash
pip install -e .[whisper]
```

---

# Usage

List courses:

```bash
course-downloader list courses.yaml
```

Synchronize all courses:

```bash
course-downloader sync courses.yaml
```

---

# Project Structure

```text
course_downloader/
├── pyproject.toml
├── README.md
├── courses.yaml
├── src/
│   └── course_downloader/
├── tests/
└── .github/
```

---

# Development

Run Ruff:

```bash
ruff check .
```

Format code:

```bash
ruff format .
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov
```

Run type checking:

```bash
mypy src
```

---

# Security

Course Downloader follows a conservative security model.

Recommendations:

- Download only trusted educational material.
- Review downloaded repositories before executing code.
- Run third-party code in isolated environments.
- Keep Git, Python and dependencies up to date.

---

# License

MIT License.
