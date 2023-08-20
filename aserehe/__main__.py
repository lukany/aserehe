import typer
from typing_extensions import Annotated

from aserehe._check import _check_git, _check_single
from aserehe._version import _current_version, _next_version

app = typer.Typer()


@app.command()
def check(from_stdin: bool = typer.Option(False, "--from-stdin")) -> None:
    if from_stdin:
        stdin = typer.get_text_stream("stdin")
        _check_single(stdin.read())
    else:
        _check_git()


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
        version_to_print = _next_version()
    else:
        version_to_print = _current_version()
    typer.echo(version_to_print)


if __name__ == "__main__":
    app()
