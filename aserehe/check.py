import re

from git import Repo

_TYPES = {
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "refactor",
    "style",
    "test",
}
_REGEX = re.compile(
    r"^(?P<type>\w+)(\((?P<scope>.*)\))?(?P<breaking>!)?: (?P<description>.+)$"
)


class InvalidCommitMessage(Exception):
    pass


class InvalidCommitType(InvalidCommitMessage):
    pass


def _check_single(message):
    match = re.match(_REGEX, message)
    if match is None:
        raise InvalidCommitMessage(f"Invalid commit message format: {message}")
    if (commit_type := match.group("type")) not in _TYPES:
        raise InvalidCommitType(f"Invalid commit type: {commit_type}")


def _check_git():
    repo = Repo(".")
    for commit in repo.iter_commits():
        _check_single(commit.summary)
