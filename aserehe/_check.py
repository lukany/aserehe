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


def _check_summary(summary: str) -> None:
    match = re.match(_REGEX, summary)
    if match is None:
        raise InvalidCommitMessage(
            f"Invalid commit summary format (first line of message): {summary}"
        )
    if (commit_type := match.group("type")) not in _TYPES:
        raise InvalidCommitType(f"Invalid commit type: {commit_type}")


def _check_single(message: str) -> None:
    if not message:
        raise InvalidCommitMessage("Empty commit message")

    lines = message.splitlines()

    _check_summary(lines[0])
    if len(lines) == 1:
        return  # summary-only commit

    if lines[1].strip():
        # "The body MUST begin one blank line after the description."
        # - https://www.conventionalcommits.org/en/v1.0.0/#specification
        # (point 6)
        raise InvalidCommitMessage(
            "Second line of commit message must be empty."
            " If you want to add a body, separate it from the summary with"
            " a blank line."
        )
    # The rest of the message (third line and beyond) is body and/or footers.
    # Those do not have to be checked as there is no incorrect format.


def _check_git() -> None:
    repo = Repo(".")
    for commit in repo.iter_commits():
        message = commit.message
        commit.summary
        if isinstance(message, bytes):
            raise TypeError("Commit message is bytes. Expected str.")
        _check_single(message)
