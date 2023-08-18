from git.repo import Repo
from semantic_version import Version  # type: ignore[import]

from aserehe._check import _check_git_commit

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


def _current_version() -> Version:
    """Return the highest semantic version tag that is an ancestor of HEAD.

    Note that the highest semantic version tag may not be the latest tag.
    """
    repo = Repo()

    parent_tags = list(
        filter(lambda tag: repo.is_ancestor(tag.commit, repo.head.commit), repo.tags)
    )

    # TODO: split into two functions
    versions: list[Version] = []
    for tag in parent_tags:
        try:
            versions.append(_parse_tag_name(tag.name))
        except ValueError:
            pass

    return max(versions, default=_INITIAL_VERSION)


def _next_version() -> Version:
    """Infer the next semantic version from conventional commit messages since the last
    version tag (considering parent tags only).
    """
    repo = Repo()
    current_version = _current_version()

    try:
        repo.head.commit
    except ValueError:
        # no commits yet
        return current_version

    # Determine the commit to stop at (the commit at the last version tag)
    current_version_tag_reference = repo.tag(f"v{current_version}")
    if current_version_tag_reference in repo.tags:
        stop_at_commit = current_version_tag_reference.commit
    else:
        stop_at_commit = None

    bump_patch = False
    bump_minor = False
    for commit in repo.iter_commits():
        if stop_at_commit is not None and commit == stop_at_commit:
            break
        conv_commit = _check_git_commit(commit)
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
