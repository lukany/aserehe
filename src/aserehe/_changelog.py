"""Changelog generation functionality."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from git import Commit
from git.refs.tag import TagReference
from git.repo import Repo
from semantic_version import Version  # type: ignore[import-untyped]

from aserehe._commit import ConventionalCommit
from aserehe._version import get_current_version, get_version_tags


@dataclass
class ChangelogEntry:
    """Represents a single changelog entry."""

    commit_type: str
    scope: str | None
    description: str
    is_breaking: bool
    commit_hash: str
    author: str
    date: datetime

    @classmethod
    def from_conventional_commit(
        cls, conventional_commit: ConventionalCommit, git_commit: Commit
    ) -> ChangelogEntry:
        """Create a changelog entry from a conventional commit and git commit."""
        # Parse scope and description from commit message
        if isinstance(git_commit.message, str):
            message_str = git_commit.message
        else:
            message_str = git_commit.message.decode('utf-8')
        scope, description = _parse_commit_message(message_str)

        return cls(
            commit_type=conventional_commit.type,
            scope=scope,
            description=description,
            is_breaking=conventional_commit.breaking,
            commit_hash=git_commit.hexsha[:8],
            author=git_commit.author.name or "Unknown",
            date=datetime.fromtimestamp(git_commit.committed_date),
        )


@dataclass
class VersionChangelog:
    """Represents changelog for a specific version."""

    version: str
    date: datetime | None
    entries: list[ChangelogEntry]

    @property
    def breaking_changes(self) -> list[ChangelogEntry]:
        """Get breaking changes."""
        return [entry for entry in self.entries if entry.is_breaking]

    @property
    def features(self) -> list[ChangelogEntry]:
        """Get features."""
        return [
            entry
            for entry in self.entries
            if entry.commit_type == "feat" and not entry.is_breaking
        ]

    @property
    def fixes(self) -> list[ChangelogEntry]:
        """Get bug fixes."""
        return [
            entry
            for entry in self.entries
            if entry.commit_type == "fix" and not entry.is_breaking
        ]

    @property
    def other_changes(self) -> list[ChangelogEntry]:
        """Get other changes (not breaking, features, or fixes)."""
        excluded_types = {"feat", "fix"}
        return [
            entry
            for entry in self.entries
            if entry.commit_type not in excluded_types and not entry.is_breaking
        ]


def _parse_commit_message(message: str) -> tuple[str | None, str]:
    """Parse scope and description from a commit message."""
    # Use the same regex as in ConventionalCommit
    summary_regex = re.compile(
        r"^(?P<type>\w+)(\((?P<scope>.*)\))?(?P<breaking>!)?: (?P<description>.+)$"
    )

    lines = message.splitlines()
    if not lines:
        return None, "No description"

    match = summary_regex.match(lines[0])
    if not match:
        return None, lines[0]  # Fallback to first line

    scope = match.group("scope")
    description = match.group("description")

    return scope, description


def get_commits_since_version(
    repo: Repo, tag_prefix: str, path: str | None = None
) -> list[Commit]:
    """Get commits since the current version tag."""
    current_version = get_current_version(repo, tag_prefix)
    version_tags = get_version_tags(repo, tag_prefix)

    # If no version tags exist, get all commits
    if not version_tags:
        if path:
            commits = list(repo.iter_commits("HEAD", paths=path))
        else:
            commits = list(repo.iter_commits("HEAD"))
        return commits

    # Find the tag for the current version
    current_tag = f"{tag_prefix}{current_version}"
    if current_tag not in [tag.name for tag in version_tags]:
        # If current version tag doesn't exist, get all commits
        if path:
            commits = list(repo.iter_commits("HEAD", paths=path))
        else:
            commits = list(repo.iter_commits("HEAD"))
        return commits

    # Get commits since the current version tag
    try:
        if path:
            commits = list(repo.iter_commits(f"{current_tag}..HEAD", paths=path))
        else:
            commits = list(repo.iter_commits(f"{current_tag}..HEAD"))
        return commits
    except Exception:
        # Fallback to all commits if range is invalid
        if path:
            commits = list(repo.iter_commits("HEAD", paths=path))
        else:
            commits = list(repo.iter_commits("HEAD"))
        return commits


def _get_commits_for_version_range(
    repo: Repo,
    tag_prefix: str,
    version: str,
    version_tags: list[TagReference],
    path: str | None,
) -> list[Commit]:
    """Get commits for a specific version range."""
    current_tag = f"{tag_prefix}{version}"

    if current_tag not in [tag.name for tag in version_tags]:
        return []

    # Find previous version to get range
    version_list = sorted(
        [Version(tag.name.removeprefix(tag_prefix)) for tag in version_tags],
        reverse=True,
    )
    current_version_obj = Version(version)

    try:
        current_index = version_list.index(current_version_obj)
        if current_index + 1 < len(version_list):
            prev_version = version_list[current_index + 1]
            prev_tag = f"{tag_prefix}{prev_version}"
            rev_range = f"{prev_tag}..{current_tag}"
        else:
            # First version, get all commits up to this tag
            rev_range = current_tag

        if path:
            return list(repo.iter_commits(rev_range, paths=path))
        return list(repo.iter_commits(rev_range))
    except (ValueError, Exception):
        return []


def generate_changelog_for_version(
    repo: Repo,
    tag_prefix: str,
    version: str | None = None,
    path: str | None = None,
    unreleased: bool = False,
) -> VersionChangelog:
    """Generate changelog for a specific version or unreleased changes."""
    if unreleased:
        # Get commits since last version
        commits = get_commits_since_version(repo, tag_prefix, path)
        version_str = "Unreleased"
        date = None
    else:
        if version is None:
            version = str(get_current_version(repo, tag_prefix))
        else:
            version = str(Version(version))  # Validate version format

        # Get commits for this version
        version_tags = get_version_tags(repo, tag_prefix)
        commits = _get_commits_for_version_range(
            repo, tag_prefix, version, version_tags, path
        )

        version_str = version
        # Get tag date
        current_tag = f"{tag_prefix}{version}"
        tag_obj = next((tag for tag in version_tags if tag.name == current_tag), None)
        date = (
            datetime.fromtimestamp(tag_obj.commit.committed_date) if tag_obj else None
        )

    # Convert commits to changelog entries
    entries = []
    for commit in commits:
        try:
            conventional_commit = ConventionalCommit.from_git_commit(commit)
            entry = ChangelogEntry.from_conventional_commit(conventional_commit, commit)
            entries.append(entry)
        except (ValueError, TypeError, AttributeError):  # nosec B112
            # Skip non-conventional commits or commits with invalid data
            continue

    return VersionChangelog(version=version_str, date=date, entries=entries)


def format_changelog_markdown(changelog: VersionChangelog) -> str:
    """Format changelog as Markdown."""
    lines = []

    # Version header
    if changelog.date:
        date_str = changelog.date.strftime("%Y-%m-%d")
        lines.append(f"## [{changelog.version}] - {date_str}")
    else:
        lines.append(f"## [{changelog.version}]")

    lines.append("")

    if not changelog.entries:
        lines.append("*No changes*")
        lines.append("")
        return "\n".join(lines)

    # Breaking changes
    if changelog.breaking_changes:
        lines.append("### ⚠ BREAKING CHANGES")
        lines.append("")
        for entry in changelog.breaking_changes:
            scope_str = f"**{entry.scope}**: " if entry.scope else ""
            lines.append(f"- {scope_str}{entry.description} ({entry.commit_hash})")
        lines.append("")

    # Features
    if changelog.features:
        lines.append("### Features")
        lines.append("")
        for entry in changelog.features:
            scope_str = f"**{entry.scope}**: " if entry.scope else ""
            lines.append(f"- {scope_str}{entry.description} ({entry.commit_hash})")
        lines.append("")

    # Bug fixes
    if changelog.fixes:
        lines.append("### Bug Fixes")
        lines.append("")
        for entry in changelog.fixes:
            scope_str = f"**{entry.scope}**: " if entry.scope else ""
            lines.append(f"- {scope_str}{entry.description} ({entry.commit_hash})")
        lines.append("")

    # Other changes
    if changelog.other_changes:
        lines.append("### Other Changes")
        lines.append("")
        for entry in changelog.other_changes:
            scope_str = f"**{entry.scope}**: " if entry.scope else ""
            type_str = entry.commit_type
            lines.append(
                f"- **{type_str}**: {scope_str}{entry.description} "
                f"({entry.commit_hash})"
            )
        lines.append("")

    return "\n".join(lines)


def generate_full_changelog(
    repo: Repo,
    tag_prefix: str,
    path: str | None = None,
    include_unreleased: bool = True,
) -> str:
    """Generate full changelog for all versions."""
    lines = ["# Changelog", ""]
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append(
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    )
    lines.append(
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    )
    lines.append("")

    # Add unreleased changes if requested
    if include_unreleased:
        unreleased = generate_changelog_for_version(
            repo, tag_prefix, path=path, unreleased=True
        )
        if unreleased.entries:
            lines.append(format_changelog_markdown(unreleased))

    # Get all version tags and sort them
    version_tags = get_version_tags(repo, tag_prefix)
    if version_tags:
        versions = sorted(
            [Version(tag.name.removeprefix(tag_prefix)) for tag in version_tags],
            reverse=True,
        )

        for version in versions:
            version_changelog = generate_changelog_for_version(
                repo, tag_prefix, str(version), path
            )
            if version_changelog.entries:
                lines.append(format_changelog_markdown(version_changelog))

    return "\n".join(lines)
