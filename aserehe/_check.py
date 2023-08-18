from git.objects import Commit
from git.repo import Repo

import re
from dataclasses import dataclass

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
_BREAKING_CHANGE_FOOTER_TOKEN_REGEX = r"BREAKING(?: |-)CHANGE"
_FOOTER_TOKEN_REGEX = (
    rf"\n"
    rf"((?:{_BREAKING_CHANGE_FOOTER_TOKEN_REGEX})|[\w-]+)"  # token
    rf"(?:(?:: )|(?: #))"  # separator
)


class InvalidSummary(Exception):
    pass


class InvalidCommitMessage(Exception):
    pass


class InvalidCommitType(InvalidCommitMessage):
    pass


@dataclass
class ConventionalCommit:
    type: str
    breaking: bool


def _check_summary(summary: str) -> ConventionalCommit:
    match = re.match(_REGEX, summary)
    if match is None:
        raise InvalidCommitMessage(
            f"Invalid commit summary format (first line of message): {summary}"
        )
    if (commit_type := str(match.group("type"))) not in _TYPES:
        raise InvalidCommitType(f"Invalid commit type: {commit_type}")

    return ConventionalCommit(type=commit_type, breaking=bool(match.group("breaking")))


def _extract_breaking_change_footer_values(message: str) -> list[str]:
    _, *footer_section = re.split(_FOOTER_TOKEN_REGEX, message)
    breaking_changes = []
    for token, value in zip(footer_section[::2], footer_section[1::2], strict=True):
        if re.match(_BREAKING_CHANGE_FOOTER_TOKEN_REGEX, token):
            breaking_changes.append(str(value))
    return breaking_changes


def _check_single(message: str) -> ConventionalCommit:
    if not message:
        raise InvalidCommitMessage("Empty commit message")

    lines = message.splitlines()

    summary_conv_commit = _check_summary(lines[0])
    if len(lines) == 1:
        return summary_conv_commit

    if lines[1].strip():
        # "The body MUST begin one blank line after the description."
        # - https://www.conventionalcommits.org/en/v1.0.0/#specification
        # (point 6)
        raise InvalidCommitMessage(
            "Second line of commit message must be empty."
            " If you want to add a body, separate it from the summary with"
            " a blank line."
        )

    breaking_changes = _extract_breaking_change_footer_values(message)

    return ConventionalCommit(
        type=summary_conv_commit.type,
        breaking=summary_conv_commit.breaking | bool(breaking_changes),
    )


def _check_git_commit(commit: Commit) -> ConventionalCommit:
    message = commit.message
    if isinstance(message, bytes):
        raise TypeError("Commit message is bytes. Expected str.")
    return _check_single(message)


def _check_git() -> None:
    repo = Repo(".")
    for commit in repo.iter_commits():
        _check_git_commit(commit)
