import pytest
from git import Repo
from pytest import MonkeyPatch
from semantic_version import Version

from aserehe._version import (
    _INITIAL_VERSION,
    _parse_tag_name,
    get_current_version,
    get_next_version,
)


@pytest.fixture
def temp_git_repo(tmp_path) -> Repo:
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path)
    config_writer = repo.config_writer()
    config_writer.set_value("user", "name", "test")
    config_writer.set_value("user", "email", "test@example.com")
    config_writer.release()

    return repo


class TestParseTagName:
    def test_valid_tag(self):
        assert _parse_tag_name("v1.2.3") == Version("1.2.3")

    def test_missing_v_prefix(self):
        with pytest.raises(ValueError, match="does not start with 'v'"):
            _parse_tag_name("1.2.3")

    def test_invalid_semver(self):
        with pytest.raises(ValueError, match="not a semantic version"):
            _parse_tag_name("vabc")


class TestGetCurrentVersion:
    def test_no_tags(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        assert get_current_version(repo=temp_git_repo) == _INITIAL_VERSION

    def test_single_tag(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        assert get_current_version(repo=temp_git_repo) == Version("1.0.0")

    def test_multiple_tags(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")

        temp_git_repo.index.commit("second commit")
        temp_git_repo.create_tag("v2.0.0")

        assert get_current_version(repo=temp_git_repo) == Version("2.0.0")


class TestGetNextVersion:
    def test_no_commits(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        assert get_next_version(repo=temp_git_repo) == _INITIAL_VERSION

    def test_feat_commit(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit("feat: add new feature")
        assert get_next_version(repo=temp_git_repo) == Version("1.1.0")

    def test_fix_commit(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit("fix: fix bug")
        assert get_next_version(repo=temp_git_repo) == Version("1.0.1")

    @pytest.mark.parametrize(
        "message",
        [
            "feat: breaking change\n\nBREAKING CHANGE: Change 1",
            "feat: breaking change\n\nBREAKING-CHANGE: Change 2",
            "feat: breaking change\n\nBREAKING CHANGE #42",
            "feat: breaking change\n\nBREAKING CHANGE # this is a breaking change",
            "\n".join(
                [
                    "feat: breaking change",
                    "",
                    "Other footer",
                    "BREAKING CHANGE: Change 4",
                    "Another footer",
                ]
            ),
            "\n".join(
                [
                    "feat: breaking change",
                    "",
                    "BREAKING CHANGE: Change 5",
                    "BREAKING CHANGE: Change 6",
                ]
            ),
        ],
    )
    def test_breaking_change_footer(
        self, temp_git_repo: Repo, monkeypatch: MonkeyPatch, message: str
    ):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit(message)
        assert get_next_version(repo=temp_git_repo) == Version("2.0.0")

    def test_breaking_change_bang(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit("feat!: another breaking change")
        assert get_next_version(repo=temp_git_repo) == Version("2.0.0")

    def test_multiple_changes(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)
        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit("feat: add new feature")
        temp_git_repo.index.commit("fix: fix bug")
        assert get_next_version(repo=temp_git_repo) == Version("1.1.0")

    def test_version_from_parent_commits_only(self, temp_git_repo: Repo, monkeypatch: MonkeyPatch):
        monkeypatch.chdir(temp_git_repo.working_dir)

        temp_git_repo.index.commit("initial commit")
        temp_git_repo.create_tag("v1.0.0")
        temp_git_repo.index.commit("feat!: breaking change")
        temp_git_repo.create_tag("v2.0.0")

        # Create a fix branch from older commit
        v1_fix_branch = temp_git_repo.create_head("v1-fix", commit="v1.0.0")
        v1_fix_branch.checkout()
        temp_git_repo.index.commit("fix: fix bug")

        assert get_next_version(repo=temp_git_repo) == Version("1.0.1")
