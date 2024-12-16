from git.repo import Repo
from semantic_version import Version  # type: ignore[import-untyped]

from aserehe._commit import ConventionalCommit

_INITIAL_VERSION = Version("0.0.0")


def _parse_tag_name(tag_name: str) -> Version:
    if not tag_name.startswith("v"):
        raise ValueError(f"The tag name {tag_name} does not start with 'v'")
    without_prefix = tag_name[1:]
    try:
        return Version(without_prefix)
    except ValueError as exc:
        raise ValueError(
            f"Tag name (without 'v' prefix) is not a semantic version: {tag_name}"
        ) from exc


def get_current_version(repo: Repo) -> Version:
    """Return the highest semantic version tag that is an ancestor of HEAD.

    Note that the highest semantic version tag may not be the latest tag.
    """
    parent_tags = filter(
        lambda tag: repo.is_ancestor(tag.commit, repo.head.commit), repo.tags
    )

    versions: list[Version] = []
    for tag in parent_tags:
        try:
            versions.append(_parse_tag_name(tag.name))
        except ValueError:
            pass

    return max(versions, default=_INITIAL_VERSION)


def get_next_version(repo: Repo) -> Version:
    """Infer the next semantic version from conventional commit messages since
    the current version.
    """
    current_version = get_current_version(repo)

    try:
        repo.head.commit
    except ValueError:
        # no commits yet
        return current_version

    current_version_tag_reference = repo.tag(f"v{current_version}")
    if current_version_tag_reference in repo.tags:
        current_version_commit = current_version_tag_reference.commit
    else:
        current_version_commit = None

    bump_patch = False
    bump_minor = False
    for commit in repo.iter_commits():
        if current_version_commit is not None and commit == current_version_commit:
            break
        conv_commit = ConventionalCommit.from_git_commit(commit)
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
