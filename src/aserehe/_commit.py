import re
from dataclasses import dataclass
from typing import Self

from git.objects import Commit

_TYPES = frozenset({"chore", "ci", "docs", "feat", "fix", "refactor", "style", "test"})
_SUMMARY = re.compile(
    r"^(?P<type>\w+)(\((?P<scope>.*)\))?(?P<breaking>!)?: (?P<description>.+)$"
)
_BREAKING_CHANGE_TOKEN = re.compile(r"BREAKING(?: |-)CHANGE")  # nosec
# A footer starts on its own line with a token followed by ": " or " #".
_FOOTER_TOKEN = re.compile(rf"\n({_BREAKING_CHANGE_TOKEN.pattern}|[\w-]+)(?:: | #)")


class InvalidCommitMessageError(Exception):
    pass


class InvalidCommitTypeError(InvalidCommitMessageError):
    pass


def _has_breaking_change_footer(message: str) -> bool:
    # re.split with a capturing group yields [text, token, text, token, ...].
    footer_tokens = _FOOTER_TOKEN.split(message)[1::2]
    return any(_BREAKING_CHANGE_TOKEN.match(token) for token in footer_tokens)


@dataclass(frozen=True)
class ConventionalCommit:
    type: str
    breaking: bool

    @classmethod
    def from_message(cls, message: str) -> Self:
        if not message:
            raise InvalidCommitMessageError("Empty commit message")

        summary, *body = message.splitlines()

        match = _SUMMARY.match(summary)
        if match is None:
            raise InvalidCommitMessageError(
                f"Invalid commit summary format (first line of message): {summary}"
            )
        if (commit_type := match.group("type")) not in _TYPES:
            raise InvalidCommitTypeError(f"Invalid commit type: {commit_type}")

        if body and body[0].strip():
            # "The body MUST begin one blank line after the description."
            # - https://www.conventionalcommits.org/en/v1.0.0/#specification
            # (point 6)
            raise InvalidCommitMessageError(
                "Second line of commit message must be empty."
                " If you want to add a body, separate it from the summary with"
                " a blank line."
            )

        return cls(
            type=commit_type,
            breaking=bool(match.group("breaking"))
            or _has_breaking_change_footer(message),
        )

    @classmethod
    def from_git_commit(cls, commit: Commit) -> Self:
        message = commit.message
        if isinstance(message, bytes):
            raise TypeError("Commit message is bytes. Expected str.")
        return cls.from_message(message)
