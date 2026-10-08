"""Module entry-point tests."""

import runpy
from unittest.mock import patch


def test_python_m_course_downloader_calls_main() -> None:
    with patch("course_downloader.cli.main") as main:
        runpy.run_module("course_downloader.__main__", run_name="__main__")
    main.assert_called_once()
