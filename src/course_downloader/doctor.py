"""Environment diagnostics."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from course_downloader.tool_checks import (
    check_tools,
)


class Doctor:
    """Run environment diagnostics."""

    def __init__(
        self,
    ) -> None:
        self.console = Console()

    def run(self) -> None:
        """Execute diagnostics."""

        table = Table(
            title="Tool Diagnostics",
        )

        table.add_column("Tool")
        table.add_column("Required")
        table.add_column("Installed")

        for tool in check_tools():
            table.add_row(
                tool.name,
                "Yes" if tool.required else "No",
                "✓" if tool.installed else "✗",
            )

        self.console.print(table)
