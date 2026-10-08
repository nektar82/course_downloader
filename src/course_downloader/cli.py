"""Command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from course_downloader.application import CourseDownloaderApplication
from course_downloader.doctor import Doctor
from course_downloader.logging_config import configure_logging
from course_downloader.models import SyncReport

console = Console()
app = typer.Typer(
    name="course-downloader",
    add_completion=False,
    help="Download and organize public educational resources.",
)


def _print_report(report: SyncReport) -> None:
    console.print(
        "Sources: "
        f"{report.succeeded} succeeded, "
        f"{report.skipped} skipped, "
        f"{report.failed} failed"
    )
    console.print(
        "Artifacts: "
        f"{report.documents_downloaded} documents downloaded, "
        f"{report.documents_converted} converted, "
        f"{report.transcripts_created} transcripts created, "
        f"{report.repositories_updated} repositories updated"
    )
    if report.warnings:
        console.print(f"[yellow]Warnings: {len(report.warnings)}[/yellow]")
        for warning in report.warnings:
            console.print(f"[yellow]- {warning}[/yellow]")


def _application(
    manifest: Path,
    course_download_root: Path | None,
    refresh: bool,
) -> CourseDownloaderApplication:
    return CourseDownloaderApplication(
        manifest,
        course_download_root_override=course_download_root,
        refresh=refresh,
    )


@app.command(name="list")
def list_courses(manifest: Path) -> None:
    """List configured courses."""

    application = CourseDownloaderApplication(manifest)
    table = Table(title="Configured Courses")
    table.add_column("Course ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")

    for course in application.list_courses():
        table.add_row(course.id, course.name, course.status or "")
    console.print(table)


@app.command()
def validate(manifest: Path) -> None:
    """Validate the manifest."""

    application = CourseDownloaderApplication(manifest)
    application.validate()
    console.print("[green]Manifest is valid.[/green]")


@app.command()
def sync(
    manifest: Path,
    course: list[str] | None = typer.Option(None, "--course"),
    tag: list[str] | None = typer.Option(None, "--tag"),
    course_download_root: Path | None = typer.Option(
        None, "--course-download-root"
    ),
    refresh: bool = typer.Option(False, "--refresh"),
) -> None:
    """Synchronize courses, optionally filtering by ID or tag."""

    application = _application(manifest, course_download_root, refresh)
    report = application.sync_all(
        course_ids=set(course or []),
        tags=set(tag or []),
    )
    _print_report(report)
    if report.failed:
        raise typer.Exit(code=1)
    console.print("[green]Synchronization complete.[/green]")


@app.command()
def sync_course(
    manifest: Path,
    course_id: str,
    course_download_root: Path | None = typer.Option(
        None, "--course-download-root"
    ),
    refresh: bool = typer.Option(False, "--refresh"),
) -> None:
    """Synchronize a single course."""

    application = _application(manifest, course_download_root, refresh)
    report = application.sync_course(course_id)
    _print_report(report)
    if report.failed:
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
