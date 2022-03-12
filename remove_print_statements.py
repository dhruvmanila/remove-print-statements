from dataclasses import dataclass, field
from typing import List, Tuple, Union

import click
import libcst as cst
import libcst.matchers as m
from libcst import RemovalSentinel, RemoveFromParent
from libcst.codemod import (
    CodemodContext,
    ContextAwareTransformer,
    TransformFailure,
    TransformSuccess,
    transform_module,
)
from libcst.metadata import PositionProvider

__version__ = "0.1.0-alpha"


@dataclass(frozen=False)
class Report:
    dry_run: bool = False
    verbose: bool = False

    # Total number of transformed files.
    file_count: int = field(init=False, default=0)

    # Total number of print statements in all files combined.
    print_statement_count: int = field(init=False, default=0)

    # Total number of files where a failure occured. The failure could occur either
    # while opening/reading the file or while transforming.
    failure_count: int = field(init=False, default=0)

    @property
    def return_code(self) -> int:
        """Return the exit code that the tool should use."""
        if self.failure_count:
            return 1
        return 0

    def __str__(self) -> str:
        """Return a one-line color summary of the report.

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

        report: List[str] = []
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
        # When in verbose mode, we want the summary to be on its own line.
        if self.verbose:
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

    @m.call_if_inside(PRINT_STATEMENT)
    def visit_Expr(self, node: cst.Expr) -> None:
        self.print_statement_count += 1
        if self.verbose:
            pos = self.get_metadata(PositionProvider, node, None)
            if pos is not None:
                click.echo(
                    f"{self.context.filename}:{pos.start.line}:{pos.start.column}: "
                    + self.module.code_for_node(node)
                )

    @m.call_if_inside(PRINT_STATEMENT)
    def leave_Expr(
        self, original_node: cst.Expr, updated_node: cst.Expr
    ) -> Union[cst.Expr, RemovalSentinel]:
        if self.dry_run:
            return updated_node
        return RemoveFromParent()


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
        with open(filename, "r") as f:
            code = f.read()
    except Exception as exc:
        click.echo(f"Could not read file {filename!r}, skipping: {exc}")
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
            if not dry_run:
                with open(filename, "w") as f:
                    f.write(result.code)
    elif isinstance(result, TransformFailure):
        click.echo(f"Failed to transform the file {filename!r}: {result.error}")
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
def main(
    dry_run: bool,
    verbose: bool,
    ignore: Tuple[str, ...],
    filenames: Tuple[str, ...],
) -> int:
    """Remove all the print statements from your Python project.

    You can preview all the print statements along with their location by
    passing both `--dry-run` and `--verbose` flags.
    """
    report = Report(dry_run=dry_run, verbose=verbose)
    for filename in filenames:
        if filename in ignore:
            continue
        check_file(filename, report=report, dry_run=dry_run, verbose=verbose)
    click.echo(report)
    return report.return_code


if __name__ == "__main__":
    raise SystemExit(main())
