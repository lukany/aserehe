from pathlib import Path

import typer
from git.repo import Repo
from typing_extensions import Annotated

from aserehe._commit import ConventionalCommit
from aserehe._version import get_current_version, get_next_version

app = typer.Typer()

_CURRENT_DIR = Path(".")


@app.command()
def check(from_stdin: bool = typer.Option(False, "--from-stdin")) -> None:
    if from_stdin:
        stdin = typer.get_text_stream("stdin")
        ConventionalCommit.from_message(stdin.read())
    else:
        repo = Repo(_CURRENT_DIR)
        for commit in repo.iter_commits():
            ConventionalCommit.from_git_commit(commit)


@app.command()
def version(
    next: Annotated[
        bool,
        typer.Option(
            "--next",
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
    repo = Repo(_CURRENT_DIR)
    version_to_print = None
    if next:
        version_to_print = get_next_version(repo)
    else:
        version_to_print = get_current_version(repo)
    typer.echo(version_to_print)
