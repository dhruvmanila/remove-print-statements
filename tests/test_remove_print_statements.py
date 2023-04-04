import sys
from typing import Mapping

import click
import pytest
from libcst.codemod import CodemodTest

from remove_print_statements import RemovePrintStatements, format_verbose_output

FILENAME = "filename"


@pytest.mark.parametrize(
    ("print_statements", "expected"),
    (
        ({}, ""),
        (
            {
                1: "print()",
            },
            "\n".join(
                [
                    FILENAME,
                    "  1 print()",
                ]
            ),
        ),
        (
            {
                1: "print(1)",
                12: "print(12)",
            },
            "\n".join(
                [
                    FILENAME,
                    "  1 print(1)",
                    "  12 print(12)",
                ]
            ),
        ),
    ),
)
def test_format_verbose_output(
    print_statements: Mapping[int, str], expected: str
) -> None:
    assert click.unstyle(format_verbose_output(FILENAME, print_statements)) == expected


class TestRemovePrintStatement(CodemodTest):
    TRANSFORM = RemovePrintStatements

    def test_noop(self) -> None:
        before = """
        """
        after = """
        """
        self.assertCodemod(before, after)

    def test_no_print_statements(self) -> None:
        before = """
            a = 5
        """
        after = """
            a = 5
        """
        self.assertCodemod(before, after)

    def test_module_level(self) -> None:
        before = """
            a = 5
            print("module scope")
            b = a + 2
        """
        after = """
            a = 5
            b = a + 2
        """
        self.assertCodemod(before, after)

    def test_main_block(self) -> None:
        before = """
        if __name__ == "__main__":
            print("in main block")
            a = 5
        """
        after = """
        if __name__ == "__main__":
            a = 5
        """
        self.assertCodemod(before, after)

    def test_in_function(self) -> None:
        before = """
        def foo():
            print("function")
            return None
        """
        after = """
        def foo():
            return None
        """
        self.assertCodemod(before, after)

    def test_in_method(self) -> None:
        before = """
        class Foo:
            def bar(self):
                print("method")
                return None
        """
        after = """
        class Foo:
            def bar(self):
                return None
        """
        self.assertCodemod(before, after)

    def test_in_property(self) -> None:
        before = """
        class Foo:
            @property
            def bar(self):
                print("property")
                return 1
        """
        after = """
        class Foo:
            @property
            def bar(self):
                return 1
        """
        self.assertCodemod(before, after)

    def test_in_for_loop(self) -> None:
        before = """
        a = 0
        for i in range(4):
            print("for loop")
            a += i
        """
        after = """
        a = 0
        for i in range(4):
            a += i
        """
        self.assertCodemod(before, after)

    def test_in_while_loop(self) -> None:
        before = """
        a = 5
        while a > 5:
            print(a)
            a -= 1
        """
        after = """
        a = 5
        while a > 5:
            a -= 1
        """
        self.assertCodemod(before, after)

    def test_in_if_statement(self) -> None:
        before = """
        x = 5
        if x == 1:
            print("if")
            a = 1
        elif x > 1:
            print("elif")
            a = 5
        else:
            print("else")
            a = 10
        """
        after = """
        x = 5
        if x == 1:
            a = 1
        elif x > 1:
            a = 5
        else:
            a = 10
        """
        self.assertCodemod(before, after)

    def test_single_statement(self) -> None:
        before = """
            def foo():
                print()


            for _ in range(5):
                print()

            if __name__ == "__main__":
                print()
            """
        after = """
            def foo():
                pass


            for _ in range(5):
                pass

            if __name__ == "__main__":
                pass
            """
        self.assertCodemod(before, after)

    # https://github.com/dhruvmanila/remove-print-statements/issues/6
    @pytest.mark.skipif(
        sys.version_info <= (3, 10),
        reason="Match statement requires Python 3.10 or higher",
    )
    def test_python_310_match_statement(self) -> None:
        before = """
            x = 2
            match x:
                case 1:
                    x -= 1
                    print("x is 1")
                case 2:
                    x -= 2
                    print("x is 2")
        """
        after = """
            x = 2
            match x:
                case 1:
                    x -= 1
                case 2:
                    x -= 2
        """
        self.assertCodemod(before, after)

    def test_dry_run(self) -> None:
        before = """
            x = 5
            print("do not remove")
            y = x + 1
        """
        after = """
            x = 5
            print("do not remove")
            y = x + 1
        """
        self.assertCodemod(before, after, dry_run=True)

    def test_utf8_characters_handled(self) -> None:
        before = """
        def foo():
            x = "“Fancy Quote”"
            print(x)
            print("“Other Fancy Quote”")
            print('"Normal Quote"')
            return x
        """
        after = """
        def foo():
            x = "“Fancy Quote”"
            return x
        """
        self.assertCodemod(before, after)
