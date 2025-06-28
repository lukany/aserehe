"""Tests for changelog generation functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

from git import Commit
from semantic_version import Version

from aserehe._changelog import (
    ChangelogEntry,
    VersionChangelog,
    format_changelog_markdown,
    get_commits_since_version,
)
from aserehe._commit import ConventionalCommit


def test_changelog_entry_from_conventional_commit():
    """Test creating a changelog entry from a conventional commit."""
    # Mock git commit
    git_commit = Mock(spec=Commit)
    git_commit.hexsha = "abcdef1234567890"
    git_commit.author.name = "Test Author"
    git_commit.committed_date = 1640995200  # 2022-01-01 00:00:00
    git_commit.message = "feat(auth): add user authentication"

    # Create conventional commit
    conventional_commit = ConventionalCommit(
        type="feat",
        breaking=False,
    )

    # Create changelog entry
    entry = ChangelogEntry.from_conventional_commit(conventional_commit, git_commit)

    assert entry.commit_type == "feat"
    assert entry.scope == "auth"
    assert entry.description == "add user authentication"
    assert entry.is_breaking is False
    assert entry.commit_hash == "abcdef12"
    assert entry.author == "Test Author"
    assert entry.date == datetime.fromtimestamp(1640995200)


def test_version_changelog_properties():
    """Test VersionChangelog properties for categorizing entries."""
    entries = [
        ChangelogEntry(
            commit_type="feat",
            scope="auth",
            description="add login",
            is_breaking=False,
            commit_hash="abc123",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="fix",
            scope="api",
            description="fix bug",
            is_breaking=False,
            commit_hash="def456",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="feat",
            scope="core",
            description="breaking change",
            is_breaking=True,
            commit_hash="ghi789",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="docs",
            scope=None,
            description="update readme",
            is_breaking=False,
            commit_hash="jkl012",
            author="Author",
            date=datetime.now(),
        ),
    ]

    changelog = VersionChangelog(version="1.0.0", date=None, entries=entries)

    assert len(changelog.breaking_changes) == 1
    assert changelog.breaking_changes[0].description == "breaking change"

    assert len(changelog.features) == 1
    assert changelog.features[0].description == "add login"

    assert len(changelog.fixes) == 1
    assert changelog.fixes[0].description == "fix bug"

    assert len(changelog.other_changes) == 1
    assert changelog.other_changes[0].description == "update readme"


def test_format_changelog_markdown():
    """Test formatting changelog as Markdown."""
    entries = [
        ChangelogEntry(
            commit_type="feat",
            scope="auth",
            description="add user authentication",
            is_breaking=False,
            commit_hash="abc123",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="fix",
            scope=None,
            description="fix critical bug",
            is_breaking=False,
            commit_hash="def456",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="feat",
            scope="core",
            description="breaking API change",
            is_breaking=True,
            commit_hash="ghi789",
            author="Author",
            date=datetime.now(),
        ),
    ]

    changelog = VersionChangelog(
        version="1.0.0",
        date=datetime(2022, 1, 1),
        entries=entries,
    )

    markdown = format_changelog_markdown(changelog)

    assert "## [1.0.0] - 2022-01-01" in markdown
    assert "### ⚠ BREAKING CHANGES" in markdown
    assert "- **core**: breaking API change (ghi789)" in markdown
    assert "### Features" in markdown
    assert "- **auth**: add user authentication (abc123)" in markdown
    assert "### Bug Fixes" in markdown
    assert "- fix critical bug (def456)" in markdown


def test_format_changelog_markdown_no_entries():
    """Test formatting changelog with no entries."""
    changelog = VersionChangelog(version="1.0.0", date=None, entries=[])
    markdown = format_changelog_markdown(changelog)

    assert "## [1.0.0]" in markdown
    assert "*No changes*" in markdown


def test_format_changelog_markdown_unreleased():
    """Test formatting unreleased changelog."""
    entries = [
        ChangelogEntry(
            commit_type="feat",
            scope="api",
            description="add new endpoint",
            is_breaking=False,
            commit_hash="abc123",
            author="Author",
            date=datetime.now(),
        ),
    ]

    changelog = VersionChangelog(version="Unreleased", date=None, entries=entries)
    markdown = format_changelog_markdown(changelog)

    assert "## [Unreleased]" in markdown
    assert "### Features" in markdown
    assert "- **api**: add new endpoint (abc123)" in markdown


@patch("aserehe._changelog.get_current_version")
@patch("aserehe._changelog.get_version_tags")
def test_get_commits_since_version_no_tags(
    mock_get_version_tags, mock_get_current_version
):
    """Test getting commits when no version tags exist."""
    mock_repo = Mock()
    mock_get_version_tags.return_value = []
    mock_get_current_version.return_value = Version("0.0.0")

    mock_commits = [Mock(), Mock()]
    mock_repo.iter_commits.return_value = mock_commits

    result = get_commits_since_version(mock_repo, "v", None)

    assert result == mock_commits
    mock_repo.iter_commits.assert_called_once_with("HEAD", paths=None)


@patch("aserehe._changelog.get_current_version")
@patch("aserehe._changelog.get_version_tags")
def test_get_commits_since_version_with_tags(
    mock_get_version_tags, mock_get_current_version
):
    """Test getting commits since version with existing tags."""
    mock_repo = Mock()
    mock_tag = Mock()
    mock_tag.name = "v1.0.0"
    mock_get_version_tags.return_value = [mock_tag]
    mock_get_current_version.return_value = Version("1.0.0")

    mock_commits = [Mock(), Mock()]
    mock_repo.iter_commits.return_value = mock_commits

    result = get_commits_since_version(mock_repo, "v", None)

    assert result == mock_commits
    mock_repo.iter_commits.assert_called_once_with("v1.0.0..HEAD", paths=None)


def test_format_changelog_other_changes():
    """Test formatting changelog with other change types."""
    entries = [
        ChangelogEntry(
            commit_type="docs",
            scope="readme",
            description="update documentation",
            is_breaking=False,
            commit_hash="abc123",
            author="Author",
            date=datetime.now(),
        ),
        ChangelogEntry(
            commit_type="style",
            scope=None,
            description="format code",
            is_breaking=False,
            commit_hash="def456",
            author="Author",
            date=datetime.now(),
        ),
    ]

    changelog = VersionChangelog(version="1.0.0", date=None, entries=entries)
    markdown = format_changelog_markdown(changelog)

    assert "### Other Changes" in markdown
    assert "- **docs**: **readme**: update documentation (abc123)" in markdown
    assert "- **style**: format code (def456)" in markdown
