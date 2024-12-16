from git.repo import Repo
from typer.testing import CliRunner

from aserehe._cli import app

runner = CliRunner()


def test_stdin(valid_message):
    result = runner.invoke(
        app, ["check", "--from-stdin"], input=valid_message["message"]
    )
    assert result.exit_code == 0

def test_check_commits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = Repo.init()

    # Valid commits should pass
    repo.index.commit("feat: add feature")
    repo.index.commit("fix: fix bug")
    repo.index.commit("docs: update readme")

    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0

    # Invalid commit should fail
    repo.index.commit("invalid commit message")
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1


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
