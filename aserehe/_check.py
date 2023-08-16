import re

from git.repo import Repo

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


def _check_single(message: str) -> None:
    summary = message.split("\n", 1)[0]
    match = re.match(_REGEX, summary)
    if match is None:
        raise InvalidCommitMessage(
            f"Invalid commit summary format (first line of message): {summary}"
        )
    if (commit_type := match.group("type")) not in _TYPES:
        raise InvalidCommitType(f"Invalid commit type: {commit_type}")


def _check_git() -> None:
    repo = Repo(".")
    for commit in repo.iter_commits():
        message = commit.message
        commit.summary
        if isinstance(message, bytes):
            raise TypeError("Commit message is bytes. Expected str.")
        _check_single(message)
