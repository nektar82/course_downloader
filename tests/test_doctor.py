"""Doctor tests."""

from unittest.mock import patch

from course_downloader.doctor import (
    Doctor,
)


@patch("course_downloader.doctor.check_tools")
def test_doctor_run(
    mock_tools,
) -> None:
    mock_tools.return_value = []

    doctor = Doctor()

    doctor.run()
