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
    version_to_print = None
    if next:
        version_to_print = _next_version()
    else:
        version_to_print = _current_version()
    typer.echo(version_to_print)


if __name__ == "__main__":
    app()
