import click
import pytest

from remove_print_statements import Report


def test_noop():
    report = Report()
    assert report.return_code == 0


@pytest.mark.parametrize(
    ("report, expected"),
    (
        (Report(dry_run=True), 0),
        (Report(dry_run=True, file_count=1, print_statement_count=2), 1),
        (Report(failure_count=1), 123),
    ),
)
def test_return_code(report: Report, expected: int) -> None:
    assert report.return_code == expected


@pytest.mark.parametrize(
    ("report, expected"),
    (
        (Report(), ""),
        (Report(dry_run=True), ""),
        (Report(verbose=True), ""),
        (
            Report(file_count=1, print_statement_count=1),
            "1 file transformed, 1 print statement removed",
        ),
        (
            Report(file_count=2, print_statement_count=4),
            "2 files transformed, 4 print statements removed",
        ),
        (
            Report(dry_run=True, file_count=1, print_statement_count=1),
            "1 file would be transformed, 1 print statement would be removed",
        ),
        (
            Report(dry_run=True, verbose=True, file_count=1, print_statement_count=1),
            "\n1 file would be transformed, 1 print statement would be removed",
        ),
        (Report(failure_count=1), "1 file failed to transform"),
        (Report(failure_count=2), "2 files failed to transform"),
        (Report(dry_run=True, failure_count=1), "1 file would fail to transform"),
        (
            Report(file_count=1, print_statement_count=1, failure_count=1),
            "1 file transformed, 1 print statement removed, 1 file failed to transform",
        ),
        (
            Report(
                dry_run=True,
                file_count=1,
                print_statement_count=2,
                failure_count=1,
            ),
            "1 file would be transformed, 2 print statements would be removed, "
            + "1 file would fail to transform",
        ),
        (
            Report(
                dry_run=True,
                verbose=True,
                file_count=2,
                print_statement_count=4,
                failure_count=2,
            ),
            "\n2 files would be transformed, 4 print statements would be removed, "
            + "2 files would fail to transform",
        ),
    ),
)
def test_summary(report: Report, expected: str) -> None:
    assert click.unstyle(str(report)) == expected
