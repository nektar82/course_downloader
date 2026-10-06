"""Tool check tests."""

from course_downloader.tool_checks import (
    check_tools,
)


def test_tool_checks() -> None:

    tools = check_tools()

    assert tools
