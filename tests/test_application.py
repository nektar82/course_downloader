"""Application tests."""

from pathlib import Path

from course_downloader.application import (
    CourseDownloaderApplication,
)


def test_application_loads(
    tmp_path: Path,
) -> None:

    manifest = tmp_path / "courses.yaml"

    manifest.write_text(
        """
courses:
  - id: test
    name: Test
    path: Test
""",
        encoding="utf-8",
    )

    application = CourseDownloaderApplication(manifest)

    assert len(application.courses) == 1


def test_prioritize_failures_orders_by_failed_count(tmp_path: Path) -> None:
    import json

    manifest = tmp_path / "courses.yaml"
    manifest.write_text(
        """
course_download_root: "CourseDownloads"
courses:
  - id: clean
    name: Clean
    path: Clean
  - id: broken
    name: Broken
    path: Broken
  - id: new
    name: New
    path: New
""",
        encoding="utf-8",
    )
    application = CourseDownloaderApplication(
        manifest, course_download_root_override=tmp_path / "CourseDownloads"
    )

    # Fake a previous report: 'broken' had failures, 'clean' did not,
    # 'new' has no report at all.
    root = tmp_path / "CourseDownloads"
    (root / "Broken" / "metadata").mkdir(parents=True)
    (root / "Broken" / "metadata" / "sync-report.json").write_text(
        json.dumps({"failed": 3}), encoding="utf-8"
    )
    (root / "Clean" / "metadata").mkdir(parents=True)
    (root / "Clean" / "metadata" / "sync-report.json").write_text(
        json.dumps({"failed": 0}), encoding="utf-8"
    )

    ordered = application._prioritize_failures(application.courses)
    assert [c.id for c in ordered] == ["broken", "clean", "new"]
