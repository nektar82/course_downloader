"""Command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from course_downloader.application import (
    CourseDownloaderApplication,
)
from course_downloader.doctor import (
    Doctor,
)
from course_downloader.logging_config import (
    configure_logging,
)

console = Console()

app = typer.Typer(
    name="course-downloader",
    add_completion=False,
    help=("Download and organize public educational resources."),
)


@app.command(name="list")
def list_courses(
    manifest: Path,
) -> None:
    """List configured courses."""

    application = CourseDownloaderApplication(manifest)

    table = Table(title="Configured Courses")

    table.add_column(
        "Course ID",
        style="cyan",
    )

    table.add_column(
        "Name",
        style="green",
    )

    table.add_column(
        "Status",
        style="yellow",
    )

    for course in application.list_courses():
        table.add_row(
            course.id,
            course.name,
            course.status or "",
        )

    console.print(table)


@app.command()
def validate(
    manifest: Path,
) -> None:
    """Validate the manifest."""

    application = CourseDownloaderApplication(manifest)

    application.validate()

    console.print("[green]Manifest is valid.[/green]")


@app.command()
def sync(
    manifest: Path,
) -> None:
    """Synchronize all courses."""

    application = CourseDownloaderApplication(manifest)
    report = application.sync_all()

    if report.failed:
        console.print(
            f"[red]Synchronization failed: {report.failed} source(s)"
            f" failed.[/red]"
        )
        raise typer.Exit(code=1)

    console.print("[green]Synchronization complete.[/green]")


@app.command()
def sync_course(
    manifest: Path,
    course_id: str,
) -> None:
    """Synchronize a single course."""

    application = CourseDownloaderApplication(manifest)
    report = application.sync_course(course_id)

    if report.failed:
        console.print(
            f"[red]Synchronization failed: {report.failed} source(s)"
            f" failed.[/red]"
        )
        raise typer.Exit(code=1)

    console.print("[green]Synchronization complete.[/green]")


@app.command()
def doctor() -> None:
    """Run diagnostics."""

    Doctor().run()


def main() -> None:
    """Application entry point."""

    configure_logging()

    app()


if __name__ == "__main__":
    main()
