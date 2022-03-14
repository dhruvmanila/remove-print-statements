<div align="center">

# remove-print-statements

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/dhruvmanila/remove-print-statements/ci?label=CI&logo=github&style=flat-square)](https://github.com/dhruvmanila/remove-print-statements/actions)
[![Codecov](https://img.shields.io/codecov/c/gh/dhruvmanila/remove-print-statements?label=codecov&logo=codecov&style=flat-square)](https://app.codecov.io/gh/dhruvmanila/remove-print-statements)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dhruvmanila/remove-print-statements/main.svg)](https://results.pre-commit.ci/latest/github/dhruvmanila/remove-print-statements/main)
[![PyPi Status](https://img.shields.io/pypi/v/remove-print-statements.svg?logo=python&logoColor=fff&style=flat-square)](https://pypi.org/project/remove-print-statements/)
![Python versions](https://img.shields.io/pypi/pyversions/remove-print-statements.svg?style=flat-square&logo=python&amp;logoColor=fff)
[![MIT License](https://img.shields.io/pypi/l/remove-print-statements.svg?style=flat-square)](./LICENSE)

A CLI tool (and pre-commit hook) to remove all the `print` statements from your
Python project.

</div>

Do you use `print` statements for debugging? We all do, and there's nothing wrong
with it. After the bug has been resolved, we need to manually open all the files
which we added the print statements in, only if we remember all of them after
hours of debugging, and remove them. A better way would be to use some sort of
find and replace from the editor or command-line, but that's still a lot of
manual work. Worst case, it gets pushed and deployed to production.

Who wants to do all the manual work in the age of automation? No one. So,
install this tool and forget about removing the print statements manually
forever. You could either run this tool manually or add it as a `pre-commit`
hook. You could even preview the print statements along with it's location
without removing it. How nice is that!

## Installation

You can install `remove-print-statements` from the Python Package Index (PyPI)
with `pip` or equivalent.

```
python -m pip install remove-print-statements
```

Or with [pre-commit](https://pre-commit.com) in the `repos` section of your
`.pre-commit-config.yaml` file ([docs](https://pre-commit.com/#plugins)):

```yaml
- repo: https://github.com/dhruvmanila/remove-print-statements
  rev: ''  # Replace with latest tag on GitHub
  hooks:
  - id: remove-print-statements
    args: ['--verbose']   # Show all the print statements to be removed
```

## Usage

Run it on a given set of files:
```sh
remove-print-statements foo.py bar.py ...
# or use globbing
remove-print-statements *.py
```

You can ignore files as well. To specify multiple files to ignore, use the flag
multiple times otherwise it's difficult to know the difference between the files
to ignore and the ones to check.
```sh
remove-print-statements *.py --ignore foo.py --ignore bar.py
```

You can preview the print statements which would be removed without modifying
the source files using both `--dry-run` and `--verbose` flags like so:

```console
$ remove-print-statements --dry-run --verbose test.py
test.py:7:0: print("module")
test.py:18:8: print("property")
test.py:27:4: print("method")
test.py:29:8: print("for loop")

1 file would be transformed, 4 print statements would be removed
```

`remove-print-statements` is a command-line tool that rewrites the files in
place. It focuses on upgrading your code and not on making it look nice. Run
remove-print-statements before formatters like [Black](https://black.readthedocs.io/en/stable/).

`remove-print-statements` does not have any ability to recurse through
directories. Use the pre-commit integration, globbing, or another technique for
applying to many files such as [with `git ls-files | xargs`][1].

### Exit status

`remove-print-statements` command returns exit statuses as follows:

| Status       | Description                                      |
| :----------: | ------------------------------------------------ |
| 0            | No print statements / changes made successfully |
| 1            | Files would be updated (dry run)                 |
| 123          | Some error happened                              |

## Development

[![packaing: poetry](https://img.shields.io/badge/packaging-poetry-299bd7?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAASCAYAAABrXO8xAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJJSURBVHgBfZLPa1NBEMe/s7tNXoxW1KJQKaUHkXhQvHgW6UHQQ09CBS/6V3hKc/AP8CqCrUcpmop3Cx48eDB4yEECjVQrlZb80CRN8t6OM/teagVxYZi38+Yz853dJbzoMV3MM8cJUcLMSUKIE8AzQ2PieZzFxEJOHMOgMQQ+dUgSAckNXhapU/NMhDSWLs1B24A8sO1xrN4NECkcAC9ASkiIJc6k5TRiUDPhnyMMdhKc+Zx19l6SgyeW76BEONY9exVQMzKExGKwwPsCzza7KGSSWRWEQhyEaDXp6ZHEr416ygbiKYOd7TEWvvcQIeusHYMJGhTwF9y7sGnSwaWyFAiyoxzqW0PM/RjghPxF2pWReAowTEXnDh0xgcLs8l2YQmOrj3N7ByiqEoH0cARs4u78WgAVkoEDIDoOi3AkcLOHU60RIg5wC4ZuTC7FaHKQm8Hq1fQuSOBvX/sodmNJSB5geaF5CPIkUeecdMxieoRO5jz9bheL6/tXjrwCyX/UYBUcjCaWHljx1xiX6z9xEjkYAzbGVnB8pvLmyXm9ep+W8CmsSHQQY77Zx1zboxAV0w7ybMhQmfqdmmw3nEp1I0Z+FGO6M8LZdoyZnuzzBdjISicKRnpxzI9fPb+0oYXsNdyi+d3h9bm9MWYHFtPeIZfLwzmFDKy1ai3p+PDls1Llz4yyFpferxjnyjJDSEy9CaCx5m2cJPerq6Xm34eTrZt3PqxYO1XOwDYZrFlH1fWnpU38Y9HRze3lj0vOujZcXKuuXm3jP+s3KbZVra7y2EAAAAAASUVORK5CYII=)](https://python-poetry.org/)
[![code style: black](https://img.shields.io/static/v1?label=code%20style&message=black&color=black&style=flat-square)](https://github.com/psf/black)
[![pre-commit: enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square)](https://github.com/pre-commit/pre-commit)

### Release

1. Run `poetry lock`
2. Bump version in `pyproject.toml` and `__version__` variable
3. Commit and push the changes with message `release: <version>`
4. Publish a new release on GitHub which will trigger an automated workflow to
   publish on PyPi

## License

remove-print-statements is licensed under the MIT License.

See [LICENSE](./LICENSE) for details.

<!-- References -->

[1]: https://adamj.eu/tech/2022/03/09/how-to-run-a-command-on-many-files-in-your-git-repository/
