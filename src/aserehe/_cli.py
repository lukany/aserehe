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
    try:
        _start, _end = revs
    except ValueError as e:
        typer.echo(
            f"Invalid revision range: {rev_range}. Expected format: START..END",
            err=True,
        )
        raise typer.Exit(code=1) from e
    for name, rev in [("START", _start), ("END", _end)]:
        try:
            repo.rev_parse(rev)
        except (BadName, BadObject) as e:
            typer.echo(f"Invalid {name} revision in rev range: '{rev}'", err=True)
            raise typer.Exit(code=1) from e


def _check_commits_fail_fast(repo: Repo, rev_range: str | None) -> None:
    """Check commits with fail-fast behavior (original behavior)."""
    for commit in repo.iter_commits(rev_range):
        try:
            ConventionalCommit.from_git_commit(commit)
        except Exception as e:
            typer.echo(f"✗ {e}", err=True)
            typer.echo(f"  Commit: {commit.hexsha[:8]} {commit.summary}", err=True)
            raise typer.Exit(code=1)


def _check_commits_with_stats(repo: Repo, rev_range: str | None) -> None:
    """Check all commits and show statistics."""
    commits = list(repo.iter_commits(rev_range))
    total_commits = len(commits)
    valid_commits = 0
    invalid_commits = []
    
    for commit in commits:
        try:
            ConventionalCommit.from_git_commit(commit)
            valid_commits += 1
        except Exception as e:
            invalid_commits.append((commit, str(e)))
    
    # Display results
    if invalid_commits:
        typer.echo("Invalid commits found:", err=True)
        for commit, error in invalid_commits:
            typer.echo(f"✗ {commit.hexsha[:8]} {commit.summary}", err=True)
            typer.echo(f"  Error: {error}", err=True)
        typer.echo()
    
    # Show statistics
    invalid_count = len(invalid_commits)
    typer.echo(f"Commit validation summary:")
    typer.echo(f"  Total commits: {total_commits}")
    typer.echo(f"  Valid commits: {valid_commits}")
    typer.echo(f"  Invalid commits: {invalid_count}")
    
    if invalid_count > 0:
        typer.echo(f"  Success rate: {valid_commits/total_commits*100:.1f}%")
        raise typer.Exit(code=1)
    else:
        typer.echo("  Success rate: 100.0%")
        typer.echo("✓ All commits are valid")


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
    no_fail_fast: bool = typer.Option(
        False,
        "--no-fail-fast",
        help=(
            "Continue checking all commits even when invalid commits are found."
            " Shows statistics at the end instead of failing on first invalid commit."
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
        if no_fail_fast:
            typer.echo(
                "Cannot use --no-fail-fast with --from-stdin. "
                "Only single commit message validation is supported.",
                err=True,
            )
            raise typer.Exit(code=1)
        stdin = typer.get_text_stream("stdin")
        try:
            ConventionalCommit.from_message(stdin.read())
            typer.echo("✓ Commit message is valid")
        except Exception as e:
            typer.echo(f"✗ {e}", err=True)
            raise typer.Exit(code=1)
    else:
        repo = Repo(_CURRENT_DIR)
        _validate_rev_range(repo=repo, rev_range=rev_range)
        
        if no_fail_fast:
            _check_commits_with_stats(repo, rev_range)
        else:
            _check_commits_fail_fast(repo, rev_range)


@app.command()
def version(
    next: Annotated[
        bool,
        typer.Option(
            "--next",
            help="Whether to print the next semantic version instead of the current",
        ),
    ] = False,
    tag_prefix: str = typer.Option(
        "v",
        "--tag-prefix",
        help="Prefix before the version in the tag name.",
    ),
    path: str | None = typer.Option(
        None,
        "--path",
        help=(
            "If specified, only commits modifying this path are considered when"
            " inferring the next version."
            " Current version is always inferred from all commits."
        ),
    ),
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
        typer.echo(
            "Cannot use --path without --next option. See --help for more information.",
            err=True,
        )
        raise typer.Exit(code=1)
    repo = Repo(_CURRENT_DIR)
    version_to_print = None
    if next:
        version_to_print = get_next_version(repo, tag_prefix, path)
    else:
        version_to_print = get_current_version(repo, tag_prefix)
    typer.echo(version_to_print)
