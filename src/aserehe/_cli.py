from pathlib import Path
from typing import Annotated, NoReturn

import typer
from git.exc import BadName, BadObject
from git.repo import Repo

from aserehe._commit import ConventionalCommit, InvalidCommitMessageError
from aserehe._version import get_current_version, get_next_version

app = typer.Typer()

_CURRENT_DIR = Path(".")


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _validate_rev_range(repo: Repo, rev_range: str) -> None:
    try:
        start, end = rev_range.split("..")
    except ValueError:
        _fail(f"Invalid revision range: {rev_range}. Expected format: START..END")
    for name, rev in (("START", start), ("END", end)):
        try:
            repo.rev_parse(rev)
        except (BadName, BadObject):
            _fail(f"Invalid {name} revision in rev range: '{rev}'")


@app.command()
def check(
    from_stdin: Annotated[
        bool,
        typer.Option(
            "--from-stdin",
            help="Read a single commit message from standard input.",
        ),
    ] = False,
    rev_range: Annotated[
        str | None,
        typer.Option(
            "--rev-range",
            help=(
                "Git revision range to check in the format START..END."
                " Both START and END must exist (e.g. HEAD~5..HEAD)"
            ),
        ),
    ] = None,
) -> None:
    """
    Check that commit messages follow the Conventional Commits specification.

    Every commit reachable from HEAD is checked unless --rev-range or --from-stdin
    is passed.
    """
    if from_stdin:
        if rev_range is not None:
            _fail(
                "Cannot use --rev-range with --from-stdin."
                " Please provide a single commit message."
            )
        try:
            ConventionalCommit.from_message(typer.get_text_stream("stdin").read())
        except InvalidCommitMessageError as error:
            _fail(str(error))
        return

    repo = Repo(_CURRENT_DIR)
    if rev_range is not None:
        _validate_rev_range(repo, rev_range)
    for commit in repo.iter_commits(rev_range):
        try:
            ConventionalCommit.from_git_commit(commit)
        except InvalidCommitMessageError as error:
            _fail(f"{commit.hexsha}: {error}")


@app.command()
def version(
    next: Annotated[
        bool,
        typer.Option(
            "--next",
            help="Whether to print the next semantic version instead of the current",
        ),
    ] = False,
    tag_prefix: Annotated[
        str,
        typer.Option("--tag-prefix", help="Prefix before the version in the tag name."),
    ] = "v",
    path: Annotated[
        str | None,
        typer.Option(
            "--path",
            help=(
                "If specified, only commits modifying this path are considered when"
                " inferring the next version."
                " Current version is always inferred from all commits."
            ),
        ),
    ] = None,
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
    if path is not None and not next:
        _fail(
            "Cannot use --path without --next option. See --help for more information."
        )
    repo = Repo(_CURRENT_DIR)
    if next:
        typer.echo(get_next_version(repo, tag_prefix, path))
    else:
        typer.echo(get_current_version(repo, tag_prefix))
