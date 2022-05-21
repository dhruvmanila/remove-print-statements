from pathlib import Path

from click.testing import CliRunner

from remove_print_statements import main


def test_noop() -> None:
    runner = CliRunner()
    result = runner.invoke(main)

    assert result.exit_code == 0
    assert not result.stdout_bytes
    assert not result.stderr_bytes


def test_verbose_output(tmp_path: str) -> None:
    runner = CliRunner()
    newlines = 10
    with runner.isolated_filesystem(tmp_path) as temp_dir:
        dir = Path(temp_dir)
        dir.joinpath("hello.py").write_text(
            'print("hello")' + "\n" * newlines + 'print("world")'
        )
        result = runner.invoke(main, ["hello.py", "--verbose"])

    assert result.exit_code == 0
    assert not result.stderr_bytes
    assert result.stdout_bytes
    assert 'hello.py\n  1 print("hello")\n  11 print("world")' in result.output


def test_ignore_single_files(tmp_path: str) -> None:
    runner = CliRunner()
    filenames = ("hello1.py", "hello2.py", "hello3.py")
    content = "print('hello')\n"

    with runner.isolated_filesystem(tmp_path) as temp_dir:
        dir = Path(temp_dir)
        for filename in filenames:
            dir.joinpath(filename).write_text(content)
        result = runner.invoke(main, ["--ignore", "hello2.py", *filenames])

    assert result.exit_code == 0
    assert not result.stderr_bytes
    assert result.stdout_bytes
    assert "2 files transformed" in result.output
    assert "2 print statements removed" in result.output
    assert content in dir.joinpath(filenames[1]).read_text()


def test_ignore_multiple_files(tmp_path: str) -> None:
    runner = CliRunner()
    filenames = ("hello1.py", "hello2.py", "hello3.py")
    content = "print('hello')\n"

    with runner.isolated_filesystem(tmp_path) as temp_dir:
        dir = Path(temp_dir)
        for filename in filenames:
            dir.joinpath(filename).write_text(content)
        result = runner.invoke(
            main, ["--ignore", "hello2.py", "--ignore", "hello3.py", *filenames]
        )

    assert result.exit_code == 0
    assert not result.stderr_bytes
    assert result.stdout_bytes
    assert "1 file transformed" in result.output
    assert "1 print statement removed" in result.output
    assert content in dir.joinpath(filenames[1]).read_text()
    assert content in dir.joinpath(filenames[2]).read_text()


def test_no_print_statements(tmp_path: str) -> None:
    runner = CliRunner()
    filenames = ("hello1.py", "hello2.py", "hello3.py")
    content = "a = 5\n"

    with runner.isolated_filesystem(tmp_path) as temp_dir:
        dir = Path(temp_dir)
        for filename in filenames:
            dir.joinpath(filename).write_text(content)
        result = runner.invoke(main, filenames)

    assert result.exit_code == 0
    assert not result.stderr_bytes
    assert result.stdout_bytes
    assert "No print statements found" in result.output


def test_transform_failure(tmp_path: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path) as temp_dir:
        dir = Path(temp_dir)
        dir.joinpath("hello.py").write_text('print("hello"\n')
        result = runner.invoke(main, ["hello.py"])

    assert result.exit_code == 123
    assert result.stdout_bytes
    assert "1 file failed to transform" in result.output
