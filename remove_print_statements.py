from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Mapping

import click
import libcst as cst
import libcst.matchers as m
from libcst.codemod import (
    CodemodContext,
    ContextAwareTransformer,
    TransformFailure,
    TransformSuccess,
    transform_module,
)
from libcst.metadata import PositionProvider

__version__ = "0.4.0"

# TODO(dhruvmanila): Remove this block when it's the default.
# https://github.com/Instagram/LibCST/issues/285#issuecomment-1011427731
if sys.version_info >= (3, 10):
    os.environ["LIBCST_PARSER_TYPE"] = "native"


@dataclass(frozen=False)
class Report:
    dry_run: bool = False
    verbose: bool = False

    # Total number of transformed files.
    file_count: int = 0

    # Total number of print statements in all files combined.
    print_statement_count: int = 0

    # Total number of files where a failure occured. The failure could occur either
    # while opening/reading the file or while transforming.
    failure_count: int = 0

    @property
    def return_code(self) -> int:
        """Return the exit code that the tool should use.

        This considers the current state of changed files and failures:
        - if there were any failures, return 123;
        - if any files were changed and --dry-run is being used, return 1;
        - otherwise return 0.
        """
        # According to http://tldp.org/LDP/abs/html/exitcodes.html starting with
        # 126 we have special return codes reserved by the shell.
        if self.failure_count:
            return 123
        elif self.file_count and self.dry_run:
            return 1
        return 0

    def __str__(self) -> str:
        """Return a one-line color summary of the report.

        The summary line consists of:
        - number of files changed
        - number of print statements removed
        - number of files failed to transform, if any.

        When `--dry-run` flag is passed, the wording of the summary line is changed
        accordingly.

        Use `click.unstyle` to remove colors.
        """
        if self.dry_run:
            transformed = "would be transformed"
            removed = "would be removed"
            failed = "would fail to transform"
        else:
            transformed = "transformed"
            removed = "removed"
            failed = "failed to transform"

        report: list[str] = []
        if self.file_count:
            s = "s" if self.file_count > 1 else ""
            report.append(
                click.style(f"{self.file_count} file{s} ", bold=True, fg="blue")
                + click.style(transformed, bold=True)
            )
        if self.print_statement_count:
            s = "s" if self.print_statement_count > 1 else ""
            report.append(
                click.style(
                    f"{self.print_statement_count} print statement{s} ",
                    bold=True,
                    fg="blue",
                )
                + click.style(removed, bold=True)
            )
        if self.failure_count:
            s = "s" if self.failure_count > 1 else ""
            report.append(
                click.style(
                    f"{self.failure_count} file{s} {failed}", bold=True, fg="red"
                )
            )

        summary = ", ".join(report)
        # When in verbose mode, the summary should be on its own line.
        if self.verbose and self.file_count:
            return "\n" + summary
        return summary


class RemovePrintStatements(ContextAwareTransformer):
    DESCRIPTION: str = "Remove all the print statements"
    METADATA_DEPENDENCIES = (PositionProvider,)

    # A matcher for the print statement.
    PRINT_STATEMENT = m.Expr(
        value=m.Call(
            func=m.Name(
                value="print",
            ),
        ),
    )

    def __init__(
        self, context: CodemodContext, *, dry_run: bool = False, verbose: bool = False
    ) -> None:
        super().__init__(context)
        self.dry_run = dry_run
        self.verbose = verbose
        self.print_statement_count = 0
        self._print_statements: dict[int, str] = {}

    @property
    def print_statements(self) -> Mapping[int, str]:
        """Return all the print statements in their code representation along with
        the line number information."""
        return self._print_statements

    @m.call_if_inside(PRINT_STATEMENT)
    def visit_Expr(self, node: cst.Expr) -> None:
        self.print_statement_count += 1
        if self.verbose:
            pos = self.get_metadata(PositionProvider, node, None)
            if pos is not None:
                self._print_statements[pos.start.line] = self.module.code_for_node(node)

    @m.call_if_inside(PRINT_STATEMENT)
    def leave_Expr(
        self, original_node: cst.Expr, updated_node: cst.Expr
    ) -> cst.Expr | cst.RemovalSentinel:
        if self.dry_run:
            return updated_node
        return cst.RemoveFromParent()


def format_verbose_output(filename: str, print_statements: Mapping[int, str]) -> str:
    """Return the formatted output used when the `--verbose` flag is provided.

    Args:
        filename: Name of the file currently being checked.
        print_statements: Mapping of line number where the print statement is
            present to the code representation of that print statement.

    Returns:
        Formatted output or an empty string if there are no print statements.
    """
    if len(print_statements) == 0:
        return ""

    result = [click.style(filename, fg="blue")]
    for start, statement in print_statements.items():
        for lineno, line in enumerate(statement.splitlines(), start=start):
            result.append(
                f"  {click.style(lineno, dim=True)} {click.style(line, bold=True)}"
            )
    return "\n".join(result)


def check_file(
    filename: str,
    *,
    report: Report,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Check the given filename updating the report.

    Args:
        filename: Name of the file to check
        report: A report instance which will be updated with the given file's stats.
        dry_run: If True, it will not update the file with the transformed code.
        verbose: If True, output all the print statements along with their location.
    """
    try:
        with open(filename) as f:
            code = f.read()
    except Exception as exc:  # pragma: no cover
        click.secho(f"Could not read file {filename!r}, skipping: {exc}", fg="red")
        report.failure_count += 1
        return

    codemod = RemovePrintStatements(
        context=CodemodContext(filename=filename),
        dry_run=dry_run,
        verbose=verbose,
    )
    result = transform_module(codemod, code=code)
    if isinstance(result, TransformSuccess):
        if codemod.print_statement_count:
            report.file_count += 1
            report.print_statement_count += codemod.print_statement_count
            if verbose:
                click.echo(format_verbose_output(filename, codemod.print_statements))
            if not dry_run:
                with open(filename, "w") as f:
                    f.write(result.code)
    elif isinstance(result, TransformFailure):
        click.secho(
            f"Failed to transform the file {filename!r}: {result.error}", fg="red"
        )
        report.failure_count += 1


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Perform a dry run without writing back the transformed file.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Preview the print statements along with their location.",
)
@click.option(
    "--ignore",
    multiple=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=False,
    ),
    help="Paths to ignore, add multiple as required.",
)
@click.version_option(
    version=__version__,
    message="%(prog)s, %(version)s",
)
@click.argument(
    "filenames",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=True,
    ),
    metavar="FILENAME ...",
)
@click.pass_context
def main(
    ctx: click.Context,
    dry_run: bool,
    verbose: bool,
    ignore: tuple[str, ...],
    filenames: tuple[str, ...],
) -> None:
    """Remove all the print statements from your Python project.

    You can preview all the print statements along with their location by
    passing both `--dry-run` and `--verbose` flags.
    """
    if not filenames:
        ctx.exit(0)

    report = Report(dry_run=dry_run, verbose=verbose)

    for filename in filenames:
        if filename in ignore:
            continue
        check_file(filename, report=report, dry_run=dry_run, verbose=verbose)

    if not (report.failure_count or report.file_count):
        click.secho("No print statements found. All good to go.", bold=True)
        ctx.exit(0)

    click.echo(str(report))
    ctx.exit(report.return_code)


if __name__ == "__main__":
    main()
