import argparse
from dataclasses import dataclass, field
from typing import Sequence, Union

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


@dataclass(frozen=False)
class Report:
    dry_run: bool = False
    verbose: bool = False
    file_count: int = field(init=False, default=0)
    print_statement_count: int = field(init=False, default=0)
    failure_count: int = field(init=False, default=0)

    @property
    def return_code(self) -> int:
        if self.failure_count:
            return 1
        return 0

    def __str__(self) -> str:
        """Return the summary report."""
        if self.dry_run:
            transformed = "would be transformed"
            removed = "would be removed"
            failed = "would fail to transform"
        else:
            transformed = "transformed"
            removed = "removed"
            failed = "failed to transform"
        report = []
        if self.file_count:
            s = "s" if self.file_count > 1 else ""
            report.append(f"{self.file_count} file{s} {transformed}")
        if self.print_statement_count:
            s = "s" if self.print_statement_count > 1 else ""
            report.append(f"{self.print_statement_count} print statement{s} {removed}")
        if self.failure_count:
            s = "s" if self.failure_count > 1 else ""
            report.append(f"{self.failure_count} file{s} {failed}")
        summary = ", ".join(report)
        if self.verbose:
            return "\n" + summary
        return summary


class RemovePrintStatements(ContextAwareTransformer):
    DESCRIPTION: str = "Remove all the print statements"
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self, context: CodemodContext, dry_run: bool = False, verbose: bool = False
    ) -> None:
        super().__init__(context)
        self.dry_run = dry_run
        self.verbose = verbose
        self.print_statement_count = 0

    @m.call_if_inside(m.Expr(value=m.Call(func=m.Name(value="print"))))
    def visit_Expr(self, node: cst.Expr) -> None:
        self.print_statement_count += 1
        if self.verbose:
            pos = self.get_metadata(PositionProvider, node, None)
            if pos is not None:
                print(
                    f"{self.context.filename}:{pos.start.line}:{pos.start.column}: "
                    + "print function called"
                )

    @m.call_if_inside(m.Expr(value=m.Call(func=m.Name(value="print"))))
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
    try:
        with open(filename, "r") as f:
            code = f.read()
    except Exception as exc:
        print(f"Could not read file {filename!r}, skipping: {exc}")
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
        print(f"Failed to transform the file {filename!r}: {result.error}")
        report.failure_count += 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        nargs="+",
        help="Python files to run the codemod on",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="only perform a dry run without writing back the transformed file",
    )
    parser.add_argument(
        "--ignore",
        nargs="+",
        type=str,
        default=[],
        action="extend",
        help="paths to ignore, add multiple as required",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show what changes are made",
    )
    args = parser.parse_args(argv)

    report = Report(dry_run=args.dry_run, verbose=args.verbose)
    for filename in args.filename:
        if filename in args.ignore:
            continue
        check_file(
            filename,
            report=report,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    print(report)
    return report.return_code


if __name__ == "__main__":
    raise SystemExit(main())
