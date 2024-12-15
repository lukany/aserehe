import re
from dataclasses import dataclass
from typing import Self

from git.objects import Commit

_BREAKING_CHANGE_FOOTER_TOKEN_REGEX = r"BREAKING(?: |-)CHANGE"
_FOOTER_TOKEN_REGEX = (
    rf"\n"
    rf"((?:{_BREAKING_CHANGE_FOOTER_TOKEN_REGEX})|[\w-]+)"  # token
    rf"(?:(?:: )|(?: #))"  # separator
)


class InvalidCommitMessageError(Exception):
    pass


class InvalidCommitTypeError(InvalidCommitMessageError):
    pass


@dataclass
class ConventionalCommit:
    type: str
    breaking: bool

    _TYPES = frozenset(
        {
            "chore",
            "ci",
            "docs",
            "feat",
            "fix",
            "refactor",
            "style",
            "test",
        }
    )
    _SUMMARY_REGEX = re.compile(
        r"^(?P<type>\w+)(\((?P<scope>.*)\))?(?P<breaking>!)?: (?P<description>.+)$"
    )

    @classmethod
    def from_summary(cls, summary: str) -> Self:
        match = re.match(cls._SUMMARY_REGEX, summary)
        if match is None:
            raise InvalidCommitMessageError(
                f"Invalid commit summary format (first line of message): {summary}"
            )
        if (commit_type := match.group("type")) not in cls._TYPES:
            raise InvalidCommitTypeError(f"Invalid commit type: {commit_type}")

        return cls(type=commit_type, breaking=bool(match.group("breaking")))

    @classmethod
    def from_message(cls, message: str) -> Self:
        if not message:
            raise InvalidCommitMessageError("Empty commit message")

        lines = message.splitlines()

        summary_conv_commit = cls.from_summary(lines[0])
        if len(lines) == 1:
            return summary_conv_commit

        if lines[1].strip():
            # "The body MUST begin one blank line after the description."
            # - https://www.conventionalcommits.org/en/v1.0.0/#specification
            # (point 6)
            raise InvalidCommitMessageError(
                "Second line of commit message must be empty."
                " If you want to add a body, separate it from the summary with"
                " a blank line."
            )

        breaking_changes = _breaking_change_footer_present(message)

        return cls(
            type=summary_conv_commit.type,
            breaking=summary_conv_commit.breaking | breaking_changes,
        )

    @classmethod
    def from_git_commit(cls, commit: Commit) -> Self:
        message = commit.message
        if isinstance(message, bytes):
            raise TypeError("Commit message is bytes. Expected str.")
        return cls.from_message(message)


def _breaking_change_footer_present(message: str) -> bool:
    _, *footer_section = re.split(_FOOTER_TOKEN_REGEX, message)
    for token, _ in zip(footer_section[::2], footer_section[1::2], strict=True):
        if re.match(_BREAKING_CHANGE_FOOTER_TOKEN_REGEX, token):
            return True
    return False
