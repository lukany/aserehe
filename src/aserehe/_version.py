from git.refs.tag import TagReference
from git.repo import Repo
from semantic_version import Version  # type: ignore[import-untyped]

from aserehe._commit import ConventionalCommit

_INITIAL_VERSION = Version("0.0.0")


def _parse_tag_name(tag_name: str, tag_prefix: str) -> Version:
    if not tag_name.startswith(tag_prefix):
        raise ValueError(f"The tag name {tag_name} does not start with '{tag_prefix}'")
    without_prefix = tag_name[len(tag_prefix) :]
    try:
        return Version(without_prefix)
    except ValueError as exc:
        raise ValueError(
            f"Tag name (without '{tag_prefix}' prefix) is not a semantic"
            f" version: {tag_name}"
        ) from exc


def _find_current_version_tag(
    repo: Repo, tag_prefix: str
) -> tuple[Version, TagReference] | None:
    """Return ``(version, tag)`` for the highest semantic version tag that is an
    ancestor of HEAD, or ``None`` if there is no such tag.

    The tag is returned alongside the version so that callers can address the
    commit it points at without rebuilding its name from the version.
    Note that the highest semantic version tag may not be the latest tag.
    """
    if not repo.head.is_valid():
        # no commits yet
        return None

    versioned_tags: list[tuple[Version, TagReference]] = []
    for tag in repo.tags:
        try:
            version = _parse_tag_name(tag.name, tag_prefix)
        except ValueError:
            continue
        if repo.is_ancestor(tag.commit, repo.head.commit):
            versioned_tags.append((version, tag))

    return max(versioned_tags, default=None, key=lambda tagged: tagged[0])


def get_current_version(repo: Repo, tag_prefix: str) -> Version:
    """Return the highest semantic version among the tags that are ancestors of
    HEAD, or 0.0.0 if none of them is a version tag.

    Note that the highest semantic version tag may not be the latest tag.
    """
    current = _find_current_version_tag(repo, tag_prefix)
    return _INITIAL_VERSION if current is None else current[0]


def get_next_version(repo: Repo, tag_prefix: str, path: str | None = None) -> Version:
    """Infer the next semantic version from conventional commit messages since
    the current version.

    For versions 0.x.x (initial development):
    - Breaking changes bump minor version
    - Features and fixes bump patch version

    For versions 1.x.x and above (stable):
    - Breaking changes bump major version
    - Features bump minor version
    - Fixes bump patch version

    If there are no commits since the current version, or no version-impacting changes,
    returns the current version.
    """
    current = _find_current_version_tag(repo, tag_prefix)
    if current is None:
        # Either there are no commits yet or none of them is tagged with a version,
        # in which case all of them are considered.
        if not repo.head.is_valid():
            return _INITIAL_VERSION
        current_version, rev_range = _INITIAL_VERSION, "HEAD"
    else:
        current_version, current_version_tag = current
        rev_range = f"{current_version_tag.commit.hexsha}..HEAD"

    bump_patch = False
    bump_minor = False
    for commit in repo.iter_commits(rev=rev_range, paths=path or ""):
        conv_commit = ConventionalCommit.from_git_commit(commit)

        # Special handling for 0.x.x versions
        if current_version.major == 0:
            if conv_commit.breaking:
                return current_version.next_minor()
            if conv_commit.type in ("fix", "feat"):
                bump_patch = True
            continue

        # Normal semver for 1.x.x and above
        if conv_commit.breaking:
            return current_version.next_major()
        if conv_commit.type == "fix":
            bump_patch = True
        if conv_commit.type == "feat":
            bump_minor = True

    if bump_minor:
        return current_version.next_minor()
    if bump_patch:
        return current_version.next_patch()
    return current_version
