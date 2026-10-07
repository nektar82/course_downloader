#!/usr/bin/env python3
"""Deprecated: Download or update a collection of educational material described in a manifest.

Supported source types:
  - course_page: crawl a public course site, save HTML, linked documents,
                 discover YouTube playlists/videos and selected GitHub repos.
  - youtube_playlist / youtube_video: transcript every lecture without opening videos.
  - github: clone or pull public repositories.
  - direct: download explicit public URLs.
  - reference: record a URL but do not scrape/download gated or interactive content.

The script never attempts to bypass authentication, paywalls, DRM, or access controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse, urlunparse

import requests
import yaml
from bs4 import BeautifulSoup

try:
    from markitdown import MarkItDown
except Exception:
    MarkItDown = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None


USER_AGENT = "CourseDownloader/1.0 (+personal educational archiving)"
DOC_EXTS = {
    ".pdf",
    ".pptx",
    ".ppt",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".epub",
    ".txt",
    ".md",
    ".csv",
    ".rtf",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".ipynb",
    ".py",
    ".key",
}
MEDIA_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".opus", ".mp4", ".webm"}
RESOURCE_EXTS = DOC_EXTS | MEDIA_EXTS
CONVERTIBLE_EXTS = {
    ".pdf",
    ".pptx",
    ".ppt",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".epub",
    ".txt",
    ".md",
    ".csv",
    ".rtf",
    ".html",
    ".htm",
}
GITHUB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)", re.I)
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


@dataclass
class Settings:
    root: Path
    timestamp_minutes: int = 5
    paragraph_chars: int = 700
    languages: tuple[str, ...] = ("en", "en-US", "en-GB")
    transcribe_if_no_captions: bool = False
    whisper_model: str = "small"
    keep_fallback_audio: bool = False
    request_delay_seconds: float = 0.15
    timeout: int = 45
    refresh: bool = False


class CourseDownloader:
    def __init__(self, settings: Settings):
        self.s = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.md = MarkItDown(enable_plugins=True) if MarkItDown else None
        self._whisper = None

    # ---------- utility ----------
    @staticmethod
    def safe_name(text: str, limit: int = 140) -> str:
        text = unquote(text or "")
        text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", text)
        text = re.sub(r"\s+", " ", text).strip().rstrip(". ")
        return (text or "untitled")[:limit]

    @staticmethod
    def slug(text: str, limit: int = 100) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        text = re.sub(r"[\s_-]+", "-", text).strip("-")
        return (text or "item")[:limit]

    @staticmethod
    def normalize_url(url: str) -> str:
        p = urlparse(url)
        p = p._replace(fragment="")
        return urlunparse(p)

    @staticmethod
    def format_ts(seconds: float) -> str:
        total = max(0, int(seconds))
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    @staticmethod
    def run(
        cmd: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )

    def course_dirs(self, course: dict[str, Any]) -> dict[str, Path]:
        base = self.s.root / Path(course["path"])
        dirs = {
            "base": base,
            "lectures": base / "lectures",
            "raw_transcripts": base / "raw" / "transcripts",
            "fallback_audio": base / "raw" / "audio",
            "web": base / "source" / "web",
            "files": base / "source" / "files",
            "repos": base / "source" / "repos",
            "markdown": base / "markdown",
            "metadata": base / "metadata",
            "logs": base / "logs",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def log(self, dirs: dict[str, Path], message: str) -> None:
        print(message)
        with (dirs["logs"] / "sync.log").open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + message + "\n")

    # ---------- Markdown conversion ----------
    def convert_file(
        self, path: Path, dirs: dict[str, Path], rel_hint: str = ""
    ) -> Path | None:
        if not self.md or path.suffix.lower() not in CONVERTIBLE_EXTS:
            return None
        try:
            result = self.md.convert(str(path))
            text = getattr(result, "markdown", None) or getattr(
                result, "text_content", None
            )
            if not text:
                return None
            rel = self.safe_name(rel_hint or path.stem)
            out = dirs["markdown"] / f"{rel}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            return out
        except Exception as exc:
            self.log(dirs, f"  MarkItDown failed for {path.name}: {exc}")
            return None

    # ---------- downloader ----------
    def download(
        self,
        url: str,
        dest_dir: Path,
        dirs: dict[str, Path],
        name_hint: str | None = None,
    ) -> Path | None:
        try:
            r = self.session.get(
                url, timeout=self.s.timeout, allow_redirects=True
            )
            r.raise_for_status()
        except Exception as exc:
            self.log(dirs, f"  Download failed: {url} :: {exc}")
            return None

        content_type = (
            (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        )
        final = r.url
        path_part = urlparse(final).path
        candidate = Path(path_part).name
        if not candidate or "." not in candidate:
            ext = {
                "application/pdf": ".pdf",
                "text/html": ".html",
                "text/plain": ".txt",
                "application/zip": ".zip",
            }.get(content_type, "")
            candidate = self.safe_name(name_hint or "download") + ext
        candidate = self.safe_name(candidate)
        dest = dest_dir / candidate

        if dest.exists() and not self.s.refresh:
            return dest
        dest.write_bytes(r.content)
        time.sleep(self.s.request_delay_seconds)
        return dest

    # ---------- course-page crawling ----------
    @staticmethod
    def is_youtube(url: str) -> bool:
        return urlparse(url).netloc.lower() in YOUTUBE_HOSTS

    @staticmethod
    def youtube_canonical(url: str) -> str:
        p = urlparse(url)
        if p.netloc.lower() == "youtu.be":
            vid = p.path.strip("/")
            return f"https://www.youtube.com/watch?v={vid}"
        return url

    @staticmethod
    def github_repo_url(url: str) -> str | None:
        m = GITHUB_RE.match(url)
        if not m:
            return None
        repo = m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://github.com/{m.group(1)}/{repo}.git"

    def page_local_name(self, url: str, fallback: str = "index") -> str:
        p = urlparse(url)
        path = p.path.strip("/") or fallback
        q = hashlib.sha1(url.encode()).hexdigest()[:8]
        name = self.safe_name(path.replace("/", "__"), 110)
        return f"{name}-{q}.html"

    def crawl_course_page(
        self, source: dict[str, Any], dirs: dict[str, Path]
    ) -> dict[str, set[str]]:
        start = source["url"]
        depth_limit = int(source.get("crawl_depth", 1))
        start_host = urlparse(start).netloc.lower()
        allowed_domains = set(source.get("allowed_domains", [])) | {start_host}
        discover_youtube = bool(source.get("discover_youtube", True))
        discover_github = bool(source.get("discover_github", True))
        download_docs = bool(source.get("download_documents", True))
        external_docs = bool(source.get("download_external_documents", True))
        include_re = (
            re.compile(source["include_regex"], re.I)
            if source.get("include_regex")
            else None
        )
        exclude_re = (
            re.compile(source["exclude_regex"], re.I)
            if source.get("exclude_regex")
            else None
        )
        document_link_re = (
            re.compile(source["document_link_regex"], re.I)
            if source.get("document_link_regex")
            else None
        )
        page_include_re = (
            re.compile(source["page_include_regex"], re.I)
            if source.get("page_include_regex")
            else None
        )

        found: dict[str, set[str]] = {
            "youtube": set(),
            "github": set(),
            "docs": set(),
            "pages": set(),
        }
        queue: list[tuple[str, int]] = [(start, 0)]
        seen: set[str] = set()

        while queue:
            url, depth = queue.pop(0)
            url = self.normalize_url(url)
            if url in seen:
                continue
            seen.add(url)
            try:
                r = self.session.get(
                    url, timeout=self.s.timeout, allow_redirects=True
                )
                r.raise_for_status()
            except Exception as exc:
                self.log(dirs, f"  Page failed: {url} :: {exc}")
                continue
            ctype = (r.headers.get("content-type") or "").lower()
            if "html" not in ctype:
                continue
            html_path = dirs["web"] / self.page_local_name(r.url)
            html_path.write_bytes(r.content)
            found["pages"].add(r.url)
            self.convert_file(html_path, dirs, "web__" + html_path.stem)
            soup = BeautifulSoup(r.content, "html.parser")

            for a in soup.find_all("a", href=True):
                href = urljoin(r.url, a.get("href"))
                href = self.normalize_url(href)
                if not href.startswith(("http://", "https://")):
                    continue
                if exclude_re and exclude_re.search(href):
                    continue
                text = " ".join(a.stripped_strings).lower()

                if discover_youtube and self.is_youtube(href):
                    found["youtube"].add(self.youtube_canonical(href))
                    continue

                repo = self.github_repo_url(href)
                if (
                    discover_github
                    and repo
                    and any(
                        k in text
                        for k in (
                            "assignment",
                            "homework",
                            "starter",
                            "code",
                            "repo",
                            "github",
                            "project",
                            "lab",
                        )
                    )
                ):
                    found["github"].add(repo)

                ext = Path(urlparse(href).path).suffix.lower()
                looks_like_resource = ext in RESOURCE_EXTS
                if document_link_re and (
                    document_link_re.search(href)
                    or document_link_re.search(text)
                ):
                    looks_like_resource = True
                if download_docs and looks_like_resource:
                    host_ok = urlparse(href).netloc.lower() in allowed_domains
                    if host_ok or external_docs:
                        if (
                            include_re is None
                            or include_re.search(href)
                            or include_re.search(text)
                        ):
                            found["docs"].add(href)
                    continue

                host = urlparse(href).netloc.lower()
                if depth < depth_limit and host in allowed_domains:
                    # Avoid obvious non-course/site-noise endpoints.
                    if not re.search(
                        r"/(login|logout|signin|signup|calendar|people|staff)(/|$)",
                        urlparse(href).path,
                        re.I,
                    ):
                        if (
                            page_include_re is None
                            or page_include_re.search(href)
                            or page_include_re.search(text)
                        ):
                            queue.append((href, depth + 1))
            time.sleep(self.s.request_delay_seconds)

        for doc in sorted(found["docs"]):
            p = self.download(doc, dirs["files"], dirs)
            if p:
                self.convert_file(p, dirs, "files__" + p.stem)

        for repo in sorted(found["github"]):
            self.clone_or_pull(repo, dirs)

        if discover_youtube:
            # Deduplicate watch URLs that belong to a playlist: ingest the playlist once.
            playlist_urls: set[str] = set()
            standalone: set[str] = set()
            for y in found["youtube"]:
                qs = parse_qs(urlparse(y).query)
                if "list" in qs and qs["list"]:
                    playlist_urls.add(
                        f"https://www.youtube.com/playlist?list={qs['list'][0]}"
                    )
                else:
                    standalone.add(y)
            for y in sorted(playlist_urls):
                self.ingest_youtube(y, dirs)
            for y in sorted(standalone):
                self.ingest_youtube(y, dirs)

        return found

    # ---------- GitHub ----------
    def clone_or_pull(self, url: str, dirs: dict[str, Path]) -> None:
        repo = self.github_repo_url(url) or url
        name = self.safe_name(Path(urlparse(repo).path).stem)
        dest = dirs["repos"] / name
        try:
            if (dest / ".git").exists():
                self.log(dirs, f"  Updating GitHub repo: {name}")
                self.run(["git", "pull", "--ff-only"], cwd=dest)
            elif not dest.exists() or self.s.refresh:
                if dest.exists() and self.s.refresh:
                    shutil.rmtree(dest)
                self.log(dirs, f"  Cloning GitHub repo: {repo}")
                self.run(["git", "clone", "--depth", "1", repo, str(dest)])
        except Exception as exc:
            self.log(dirs, f"  GitHub failed: {repo} :: {exc}")

    # ---------- YouTube ----------
    def yt_entries(self, url: str) -> tuple[str, list[dict[str, Any]]]:
        proc = self.run(
            ["yt-dlp", "--flat-playlist", "--dump-single-json", url]
        )
        data = json.loads(proc.stdout)
        title = data.get("title") or "YouTube"
        entries = data.get("entries")
        if entries:
            return title, entries
        # Single video metadata can still be represented as one entry.
        return title, [data]

    def choose_transcript(self, video_id: str):
        if YouTubeTranscriptApi is None:
            raise RuntimeError("youtube-transcript-api is not installed")

        api = YouTubeTranscriptApi()
        if hasattr(api, "list"):
            tlist = api.list(video_id)
        else:  # compatibility with older releases
            tlist = YouTubeTranscriptApi.list_transcripts(video_id)

        langs = list(self.s.languages)
        for method_name in (
            "find_manually_created_transcript",
            "find_generated_transcript",
            "find_transcript",
        ):
            method = getattr(tlist, method_name, None)
            if method:
                try:
                    return method(langs)
                except Exception:
                    pass

        # Last resort: first available transcript, translated to English if supported.
        for t in tlist:
            try:
                if getattr(t, "is_translatable", False):
                    return t.translate("en")
            except Exception:
                pass
            return t
        raise RuntimeError("No transcript is available")

    @staticmethod
    def segments_to_dicts(fetched: Any) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for seg in fetched:
            if isinstance(seg, dict):
                out.append(
                    {
                        "text": seg.get("text", ""),
                        "start": float(seg.get("start", 0.0)),
                        "duration": float(seg.get("duration", 0.0)),
                    }
                )
            else:
                out.append(
                    {
                        "text": getattr(seg, "text", ""),
                        "start": float(getattr(seg, "start", 0.0)),
                        "duration": float(getattr(seg, "duration", 0.0)),
                    }
                )
        return out

    def transcript_markdown(self, segments: list[dict[str, Any]]) -> str:
        interval = self.s.timestamp_minutes * 60
        next_heading = 0.0
        out: list[str] = []
        para: list[str] = []
        char_count = 0
        last_end = 0.0

        def flush() -> None:
            nonlocal para, char_count
            if not para:
                return
            text = " ".join(para)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                out.extend([text, ""])
            para = []
            char_count = 0

        for seg in segments:
            text = re.sub(r"\s+", " ", str(seg.get("text", ""))).strip()
            if not text:
                continue
            start = float(seg.get("start", 0.0))
            duration = float(seg.get("duration", 0.0))
            gap = max(0.0, start - last_end)

            if start >= next_heading:
                flush()
                out.extend([f"### {self.format_ts(start)}", ""])
                while next_heading <= start:
                    next_heading += interval

            # A noticeable caption gap is often a useful paragraph boundary.
            if gap >= 2.2:
                flush()

            para.append(text)
            char_count += len(text) + 1
            sentence_end = bool(re.search(r"[.!?][\"\'”’)]?$", text))
            if (
                char_count >= self.s.paragraph_chars
                and sentence_end
                or char_count >= self.s.paragraph_chars * 2
            ):
                flush()

            last_end = max(last_end, start + duration)

        flush()
        return "\n".join(out).strip()

    def whisper_transcribe(
        self, video_id: str, dirs: dict[str, Path]
    ) -> list[dict[str, Any]]:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError(
                "ffmpeg is required for the no-caption audio fallback"
            )
        try:
            from faster_whisper import WhisperModel
        except Exception as exc:
            raise RuntimeError(
                "Install faster-whisper for no-caption transcription"
            ) from exc

        audio_template = dirs["fallback_audio"] / f"{video_id}.%(ext)s"
        self.run(
            [
                "yt-dlp",
                "-f",
                "bestaudio/best",
                "--extract-audio",
                "--audio-format",
                "wav",
                "-o",
                str(audio_template),
                f"https://www.youtube.com/watch?v={video_id}",
            ]
        )
        audio = dirs["fallback_audio"] / f"{video_id}.wav"
        if not audio.exists():
            matches = list(dirs["fallback_audio"].glob(video_id + ".*"))
            if not matches:
                raise RuntimeError(
                    "yt-dlp did not produce a fallback audio file"
                )
            audio = matches[0]

        if self._whisper is None:
            self._whisper = WhisperModel(
                self.s.whisper_model, device="auto", compute_type="auto"
            )
        segments, _info = self._whisper.transcribe(str(audio), vad_filter=True)
        out = [
            {
                "text": s.text.strip(),
                "start": float(s.start),
                "duration": float(s.end - s.start),
            }
            for s in segments
        ]
        if not self.s.keep_fallback_audio:
            try:
                audio.unlink()
            except OSError:
                pass
        return out

    def ingest_youtube(self, url: str, dirs: dict[str, Path]) -> None:
        try:
            playlist_title, entries = self.yt_entries(url)
        except Exception as exc:
            self.log(dirs, f"  YouTube enumeration failed: {url} :: {exc}")
            return

        width = max(2, len(str(len(entries))))
        for pos, entry in enumerate(entries, 1):
            video_id = entry.get("id")
            if not video_id:
                continue
            title = entry.get("title") or f"Lecture {pos}"
            out_name = f"{pos:0{width}d}-{self.slug(title)}.md"
            out_path = dirs["lectures"] / out_name
            raw_path = (
                dirs["raw_transcripts"] / f"{pos:0{width}d}-{video_id}.json"
            )
            if out_path.exists() and raw_path.exists() and not self.s.refresh:
                continue

            self.log(dirs, f"  [{pos}/{len(entries)}] {title}")
            source_kind = "YouTube captions"
            caption_language = "unknown"
            caption_type = "unknown"
            try:
                transcript = self.choose_transcript(video_id)
                fetched = transcript.fetch(preserve_formatting=True)
                segments = self.segments_to_dicts(fetched)
                caption_language = str(
                    getattr(transcript, "language", "unknown")
                )
                caption_type = (
                    "generated"
                    if getattr(transcript, "is_generated", False)
                    else "manual"
                )
            except Exception as exc:
                if not self.s.transcribe_if_no_captions:
                    self.log(dirs, f"    Transcript unavailable: {exc}")
                    continue
                try:
                    self.log(
                        dirs,
                        "    No captions; falling back to local Whisper transcription",
                    )
                    segments = self.whisper_transcribe(video_id, dirs)
                    source_kind = "Local Whisper transcription"
                    caption_language = "auto-detected"
                    caption_type = "local ASR"
                except Exception as wexc:
                    self.log(dirs, f"    Audio fallback failed: {wexc}")
                    continue

            raw_path.write_text(
                json.dumps(segments, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            body = self.transcript_markdown(segments)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            doc = (
                f"# {title}\n\n"
                f"Playlist/course: {playlist_title}\n\n"
                f"Lecture number: {pos}\n\n"
                f"Video: {video_url}\n\n"
                f"Transcript source: {source_kind}\n\n"
                f"Language: {caption_language}\n\n"
                f"Caption/transcription type: {caption_type}\n\n"
                f"## Transcript\n\n{body}\n"
            )
            out_path.write_text(doc, encoding="utf-8")

    # ---------- direct/reference ----------
    def ingest_direct(
        self, source: dict[str, Any], dirs: dict[str, Path]
    ) -> None:
        urls = source.get("urls") or (
            [source["url"]] if source.get("url") else []
        )
        for url in urls:
            p = self.download(url, dirs["files"], dirs)
            if p:
                self.convert_file(p, dirs, "files__" + p.stem)

    # ---------- index ----------
    def write_index(
        self, course: dict[str, Any], dirs: dict[str, Path]
    ) -> None:
        lines = [f"# {course['name']}", ""]
        if course.get("status"):
            lines += [f"Curriculum status: {course['status']}", ""]
        if course.get("why"):
            lines += [course["why"], ""]
        lines += ["## Lectures", ""]
        lectures = sorted(dirs["lectures"].glob("*.md"))
        if lectures:
            lines += [f"- [{p.stem}](lectures/{p.name})" for p in lectures]
        else:
            lines.append("No public lecture transcripts downloaded yet.")
        lines += ["", "## Converted material", ""]
        converted = sorted(dirs["markdown"].glob("*.md"))
        if converted:
            lines += [f"- [{p.stem}](markdown/{p.name})" for p in converted]
        else:
            lines.append("No converted documents yet.")
        refs = []
        for src in course.get("sources", []):
            if src.get("url"):
                refs.append(
                    (src.get("label") or src.get("type", "source"), src["url"])
                )
            for u in src.get("urls", []) or []:
                refs.append((src.get("label") or src.get("type", "source"), u))
        if refs:
            lines += ["", "## Source references", ""]
            for label, url in refs:
                lines.append(f"- {label}: {url}")
        (dirs["base"] / "README.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        (dirs["metadata"] / "course.json").write_text(
            json.dumps(course, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def sync_course(self, course: dict[str, Any]) -> None:
        dirs = self.course_dirs(course)
        self.log(dirs, f"\n=== {course['name']} ===")
        for source in course.get("sources", []):
            st = source.get("type")
            try:
                if st == "course_page":
                    self.crawl_course_page(source, dirs)
                elif st in {"youtube_playlist", "youtube_video"}:
                    self.ingest_youtube(source["url"], dirs)
                elif st == "github":
                    self.clone_or_pull(source["url"], dirs)
                elif st == "direct":
                    self.ingest_direct(source, dirs)
                elif st == "reference":
                    self.log(
                        dirs,
                        f"  Reference only (not scraped): {source.get('url', '')}",
                    )
                else:
                    self.log(dirs, f"  Unknown source type: {st}")
            except Exception as exc:
                self.log(dirs, f"  Source failed ({st}): {exc}")
        self.write_index(course, dirs)


def load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "courses" not in data:
        raise ValueError("Manifest must contain a top-level 'courses' list")
    return data


def build_settings(data: dict[str, Any], args: argparse.Namespace) -> Settings:
    defaults = data.get("defaults", {})
    root = Path(args.root or data.get("library_root") or "Courses").expanduser()
    return Settings(
        root=root,
        timestamp_minutes=int(defaults.get("timestamp_minutes", 5)),
        paragraph_chars=int(defaults.get("paragraph_chars", 700)),
        languages=tuple(defaults.get("languages", ["en", "en-US", "en-GB"])),
        transcribe_if_no_captions=bool(
            defaults.get("transcribe_if_no_captions", False)
            or args.whisper_fallback
        ),
        whisper_model=str(defaults.get("whisper_model", "small")),
        keep_fallback_audio=bool(defaults.get("keep_fallback_audio", False)),
        request_delay_seconds=float(
            defaults.get("request_delay_seconds", 0.15)
        ),
        timeout=int(defaults.get("timeout", 45)),
        refresh=bool(args.refresh),
    )


def check_tools() -> list[str]:
    messages = []
    for exe in ("yt-dlp", "git"):
        if shutil.which(exe) is None:
            messages.append(f"WARNING: {exe} not found on PATH")
    if shutil.which("ffmpeg") is None:
        messages.append(
            "NOTE: ffmpeg not found; caption-based YouTube transcripts still work, but no-caption audio fallback will not"
        )
    if MarkItDown is None:
        messages.append(
            "WARNING: markitdown Python package not importable; files will download but not convert"
        )
    if YouTubeTranscriptApi is None:
        messages.append(
            "WARNING: youtube-transcript-api not importable; YouTube captions cannot be fetched"
        )
    return messages


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build/update a Markdown course library"
    )
    ap.add_argument("manifest", type=Path, help="YAML course manifest")
    ap.add_argument(
        "--course",
        action="append",
        help="Only sync a specific course id (repeatable)",
    )
    ap.add_argument(
        "--tag",
        action="append",
        help="Only sync courses carrying this tag (repeatable; any matching tag is selected)",
    )
    ap.add_argument("--root", help="Override library root directory")
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="Redownload/reconvert existing items",
    )
    ap.add_argument(
        "--whisper-fallback",
        action="store_true",
        help="Transcribe YouTube audio locally when captions are absent",
    )
    ap.add_argument(
        "--list", action="store_true", help="List manifest courses and exit"
    )
    args = ap.parse_args()

    data = load_manifest(args.manifest)
    if args.list:
        for c in data["courses"]:
            tags = ",".join(c.get("tags", []))
            suffix = f" tags={tags}" if tags else ""
            print(f"{c['id']}: {c['name']} [{c.get('status', '')}]" + suffix)
        return 0

    for m in check_tools():
        print(m, file=sys.stderr)

    downloader = CourseDownloader(build_settings(data, args))
    wanted = set(args.course or [])
    wanted_tags = set(args.tag or [])
    courses = [c for c in data["courses"] if not wanted or c["id"] in wanted]
    if wanted_tags:
        courses = [
            c
            for c in courses
            if wanted_tags.intersection(set(c.get("tags", [])))
        ]
    missing = wanted - {c["id"] for c in courses}
    if missing:
        raise SystemExit("Unknown course id(s): " + ", ".join(sorted(missing)))

    for course in courses:
        downloader.sync_course(course)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
