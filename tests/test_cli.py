from pathlib import Path

from git.repo import Repo
from typer.testing import CliRunner

from aserehe._cli import app

runner = CliRunner()


def _output(*args: str) -> str:
    return runner.invoke(app, list(args)).output.strip()


def test_stdin(valid_message):
    result = runner.invoke(app, ["check", "--from-stdin"], input=valid_message.message)
    assert result.exit_code == 0


def test_invalid_args(git_repo: Repo):
    git_repo.index.commit("feat: add feature")

    # Sanity check
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0

    # Using --from-stdin with --rev-range should fail
    result = runner.invoke(
        app,
        ["check", "--from-stdin", "--rev-range", "HEAD~..HEAD"],
        input="fix: the bug",
    )
    assert result.exit_code == 1
    assert "Cannot use --rev-range with --from-stdin" in result.output


def test_check_commits(git_repo: Repo):
    # Valid commits should pass
    git_repo.index.commit("feat: add feature")
    git_repo.index.commit("fix: fix bug")
    git_repo.index.commit("docs: update readme")

    # Invalid rev range should fail
    result = runner.invoke(app, ["check", "--rev-range", "HEAD~100..HEAD"])
    assert result.exit_code == 1

    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0

    # Invalid commit should fail
    git_repo.index.commit("invalid commit message")
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1

    # ... but not when it is outside of the checked range
    result = runner.invoke(app, ["check", "--rev-range", "HEAD~3..HEAD~"])
    assert result.exit_code == 0, result.output


def test_check_reports_invalid_commit(git_repo: Repo):
    git_repo.index.commit("not conventional")

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    # The error is reported, not raised as an unhandled traceback.
    assert isinstance(result.exception, SystemExit)
    assert git_repo.head.commit.hexsha in result.output
    assert "Invalid commit summary format" in result.output


def test_check_stdin_reports_invalid_message():
    result = runner.invoke(app, ["check", "--from-stdin"], input="not conventional")

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Invalid commit summary format" in result.output


def test_version(git_repo: Repo):
    assert _output("version") == _output("version", "--next") == "0.0.0"
    git_repo.index.commit("feat: add feature")

    git_repo.create_tag("v1.0.0")
    assert _output("version") == "1.0.0"

    git_repo.index.commit("fix: fix bug")
    assert _output("version", "--next") == "1.0.1"

    git_repo.index.commit("test: add test")
    git_repo.index.commit("ci: add CI")
    git_repo.index.commit("docs: add docs")
    assert _output("version", "--next") == "1.0.1"

    git_repo.index.commit("feat: add another feature")
    assert _output("version", "--next") == "1.1.0"

    git_repo.index.commit("chore!: drop support for Python 2")
    assert _output("version", "--next") == "2.0.0"

    git_repo.create_tag("v2.0.0")
    assert _output("version") == _output("version", "--next") == "2.0.0"

    git_repo.head.reset("HEAD~1", index=True, working_tree=True)
    assert _output("version") == "1.0.0"
    assert _output("version", "--next") == "1.1.0"


def test_version_with_path(git_repo: Repo, tmp_path: Path):
    """The --path option restricts the bump to commits touching that path."""
    git_repo.index.commit("chore: initial commit")
    git_repo.create_tag("v1.0.0")

    for name, message in [
        ("a.txt", "fix: fix bug in a"),
        ("b.txt", "feat: add feature in b"),
        ("c.txt", "feat!: add breaking feature in c"),
    ]:
        (tmp_path / name).write_text(name)
        git_repo.index.add([name])
        git_repo.index.commit(message)

    assert _output("version", "--next") == "2.0.0"
    assert _output("version", "--next", "--path", "a.txt") == "1.0.1"
    assert _output("version", "--next", "--path", "b.txt") == "1.1.0"
    assert _output("version", "--next", "--path", "c.txt") == "2.0.0"
    assert _output("version", "--next", "--path", "nonexistent.txt") == "1.0.0"
