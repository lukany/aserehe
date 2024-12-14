import typer
from typing_extensions import Annotated

from aserehe._check import parse_git_history, ConventionalCommit
from aserehe._version import current_version, next_version

app = typer.Typer()


@app.command()
def check(from_stdin: bool = typer.Option(False, "--from-stdin")) -> None:
    if from_stdin:
        stdin = typer.get_text_stream("stdin")
        ConventionalCommit.from_message(stdin.read())
    else:
        parse_git_history()


@app.command()
def version(
    next: Annotated[
        bool,
        typer.Option(
            "--next",
            is_flag=True,
            help="Whether to print the next semantic version instead of the current",
        ),
    ] = False,
) -> None:
    """
    Print the current or next version. A current version is printed unless --next option
    is passed in which case the next semantic version is printed.

    The current version is inferred from the latest git tag in the current and parent
    commits.

    The next semantic version is inferred from the conventional commits since the commit
    tagged with the current version.
    E.g. if the current version is 1.0.0 and there is a descendant conventional commit
    with a breaking change, the next version will be 2.0.0.
    """
    version_to_print = None
    if next:
        version_to_print = next_version()
    else:
        version_to_print = current_version()
    typer.echo(version_to_print)


if __name__ == "__main__":
    app()
