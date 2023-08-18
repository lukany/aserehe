from git.repo import Repo
from semantic_version import Version

from aserehe._version import _current_version, _next_version


def test_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = Repo.init()
    assert _current_version() == _next_version() == Version("0.0.0")
    repo.index.commit("feat: add feature")

    repo.create_tag("v1.0.0")
    assert _current_version() == Version("1.0.0")

    repo.index.commit("fix: fix bug")
    assert _next_version() == Version("1.0.1")

    repo.index.commit("test: add test")
    repo.index.commit("ci: add CI")
    repo.index.commit("docs: add docs")
    assert _next_version() == Version("1.0.1")

    repo.index.commit("feat: add another feature")
    assert _next_version() == Version("1.1.0")

    repo.index.commit("chore!: drop support for Python 2")
    assert _next_version() == Version("2.0.0")

    repo.create_tag("v2.0.0")
    assert _current_version() == _next_version() == Version("2.0.0")

    repo.head.reset("HEAD~1", index=True, working_tree=True)
    assert _current_version() == Version("1.0.0")
    assert _next_version() == Version("1.1.0")
