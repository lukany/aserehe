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


def get_current_version(repo: Repo, tag_prefix: str) -> Version:
    """Return the highest semantic version tag that is an ancestor of HEAD.

    Note that the highest semantic version tag may not be the latest tag.
    """
    parent_tags = filter(
        lambda tag: repo.is_ancestor(tag.commit, repo.head.commit), repo.tags
    )

    versions: list[Version] = []
    for tag in parent_tags:
        try:
            versions.append(_parse_tag_name(tag.name, tag_prefix))
        except ValueError:
            pass

    return max(versions, default=_INITIAL_VERSION)


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
    current_version = get_current_version(repo, tag_prefix)

    try:
        repo.head.commit
    except ValueError:
        # no commits yet
        return current_version

    rev_range = "..HEAD"

    current_version_tag_reference = repo.tag(f"v{current_version}")
    if current_version_tag_reference in repo.tags:
        rev_range = current_version_tag_reference.commit.hexsha + rev_range

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
