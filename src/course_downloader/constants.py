"""Application constants."""

from course_downloader import __version__

USER_AGENT = f"CourseDownloader/{__version__} (personal educational archiving)"
DEFAULT_TIMEOUT = 45
MAX_DOWNLOAD_SIZE_MB = 500
DEFAULT_MAX_PAGES = 500
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 1.0
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}
