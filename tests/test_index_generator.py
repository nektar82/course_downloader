"""Index generation tests."""

from pathlib import Path

from course_downloader.index_generator import (
    IndexGenerator,
)
from course_downloader.models import (
    Course,
)


def test_readme_generation(
    tmp_path: Path,
) -> None:

    course = Course(
        id="example",
        name="Example",
        path="Example",
    )

    readme = tmp_path / "README.md"

    generator = IndexGenerator()

    generator.write_course_readme(
        course,
        readme,
    )

    assert readme.exists()
