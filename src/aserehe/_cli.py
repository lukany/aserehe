from pathlib import Path

import typer
from git.repo import Repo
from gitdb.exc import BadName, BadObject  # type: ignore[import-untyped]
from typing_extensions import Annotated

from aserehe._commit import ConventionalCommit
from aserehe._version import get_current_version, get_next_version

app = typer.Typer()

_CURRENT_DIR = Path(".")


def _validate_rev_range(repo: Repo, rev_range: str | None) -> None:
    if rev_range is None:
        return
    revs = rev_range.split("..")
    if len(revs) != 2 or not revs[0] or not revs[1]:
        typer.echo(
            f"Invalid revision range: {rev_range}. Expected format: START..END",
            err=True,
        )
        raise typer.Exit(code=1)
    for rev in revs:
        try:
            repo.rev_parse(rev)
        except (BadName, BadObject) as e:
            typer.echo(f"Invalid revision: '{rev}'", err=True)
            raise typer.Exit(code=1) from e

@app.command()
def check(
    from_stdin: bool = typer.Option(False, "--from-stdin"),
    rev_range: str | None = typer.Option(
        None,
        "--rev-range",
        help=(
            "Git revision range to check in the format START..END."
            " Both START and END must exist (e.g. HEAD~5..HEAD)"
        ),
    ),
) -> None:
    if from_stdin:
        if rev_range is not None:
            typer.echo(
                "Cannot use --rev-range with --from-stdin. "
                "Please provide a single commit message.",
                err=True,
            )
            raise typer.Exit(code=1)
        stdin = typer.get_text_stream("stdin")
        ConventionalCommit.from_message(stdin.read())
    else:
        repo = Repo(_CURRENT_DIR)
        _validate_rev_range(repo=repo, rev_range=rev_range)
        for commit in repo.iter_commits(rev_range):
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
