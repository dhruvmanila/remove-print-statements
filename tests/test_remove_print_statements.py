import io
from unittest.mock import patch

from libcst.codemod import CodemodTest

from remove_print_statements import RemovePrintStatements


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

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_verbose(self, mock_out: io.StringIO) -> None:
        before = """
            x = 5
            print("verbose")
            y = x + 1
        """
        after = """
            x = 5
            y = x + 1
        """
        self.assertCodemod(before, after, verbose=True)
        self.assertEqual(mock_out.getvalue(), 'None:2:0: print("verbose")\n')

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_dry_run_and_verbose(self, mock_out: io.StringIO) -> None:
        before = """
            x = 5
            print("verbose")
            y = x + 1
        """
        after = """
            x = 5
            print("verbose")
            y = x + 1
        """
        self.assertCodemod(before, after, dry_run=True, verbose=True)
        self.assertEqual(mock_out.getvalue(), 'None:2:0: print("verbose")\n')
