from git.repo import Repo
from typer.testing import CliRunner

from aserehe._cli import app

runner = CliRunner()


def test_stdin(valid_message):
    result = runner.invoke(
        app, ["check", "--from-stdin"], input=valid_message["message"]
    )
    assert result.exit_code == 0


def test_invalid_args(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = Repo.init()
    repo.index.commit("feat: add feature")

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


def test_check_commits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = Repo.init()

    # Valid commits should pass
    repo.index.commit("feat: add feature")
    repo.index.commit("fix: fix bug")
    repo.index.commit("docs: update readme")

    # Invalid rev range should fail
    result = runner.invoke(app, ["check", "--rev-range", "HEAD~100..HEAD"])
    assert result.exit_code == 1

    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0

    # Invalid commit should fail
    repo.index.commit("invalid commit message")
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1

    result = runner.invoke(app, ["check", "--rev-range", "HEAD~3..HEAD~"])
    assert (
        result.exit_code == 0
    ), f"Expected exit code 0 but got {result.exit_code}. Output: {result.output}"


def test_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = Repo.init()

    def _invoke_return_output(command: list[str]) -> str:
        return runner.invoke(app, command).output.strip()  # output contains a newline

    def current_version_cmd():
        return _invoke_return_output(["version"])

    def next_version_cmd():
        return _invoke_return_output(["version", "--next"])

    assert current_version_cmd() == next_version_cmd() == "0.0.0"
    repo.index.commit("feat: add feature")

    repo.create_tag("v1.0.0")
    assert current_version_cmd() == "1.0.0"

    repo.index.commit("fix: fix bug")
    assert next_version_cmd() == "1.0.1"

    repo.index.commit("test: add test")
    repo.index.commit("ci: add CI")
    repo.index.commit("docs: add docs")
    assert next_version_cmd() == "1.0.1"

    repo.index.commit("feat: add another feature")
    assert next_version_cmd() == "1.1.0"

    repo.index.commit("chore!: drop support for Python 2")
    assert next_version_cmd() == "2.0.0"

    repo.create_tag("v2.0.0")
    assert current_version_cmd() == next_version_cmd() == "2.0.0"

    repo.head.reset("HEAD~1", index=True, working_tree=True)
    assert current_version_cmd() == "1.0.0"
    assert next_version_cmd() == "1.1.0"


def test_version_with_path(tmp_path, monkeypatch):
    """Test that the --path option filters commits affecting only the specified path."""
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    repo = Repo.init(tmp_path)

    repo.index.commit("chore: initial commit")
    repo.create_tag("v1.0.0")

    a_file = tmp_path / "a.txt"
    a_file.write_text("content a")
    repo.index.add([str(a_file)])
    repo.index.commit("fix: fix bug in a")

    b_file = tmp_path / "b.txt"
    b_file.write_text("content b")
    repo.index.add([str(b_file)])
    repo.index.commit("feat: add feature in b")

    c_file = tmp_path / "c.txt"
    c_file.write_text("content c")
    repo.index.add([str(c_file)])
    repo.index.commit("feat!: add breaking feature in c")

    out_all = runner.invoke(app, ["version", "--next"]).output.strip()
    out_a = runner.invoke(app, ["version", "--next", "--path", "a.txt"]).output.strip()
    out_b = runner.invoke(app, ["version", "--next", "--path", "b.txt"]).output.strip()
    out_c = runner.invoke(app, ["version", "--next", "--path", "c.txt"]).output.strip()
    out_none = runner.invoke(
        app, ["version", "--next", "--path", "nonexistent.txt"]
    ).output.strip()

    assert (
        out_all == "2.0.0"
    ), f"Expected 2.0.0 when considering all commits, got {out_all}"
    assert (
        out_a == "1.0.1"
    ), f"Expected 1.0.1 when considering commits for a.txt, got {out_a}"
    assert (
        out_b == "1.1.0"
    ), f"Expected 1.1.0 when considering commits for b.txt, got {out_b}"
    assert (
        out_c == "2.0.0"
    ), f"Expected 2.0.0 when considering commits for c.txt, got {out_c}"
    assert (
        out_none == "1.0.0"
    ), f"Expected 1.0.0 when no commits match the path, got {out_none}"
