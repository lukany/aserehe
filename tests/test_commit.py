import pytest

from aserehe._commit import (
    ConventionalCommit,
    InvalidCommitMessageError,
    InvalidCommitTypeError,
    _breaking_change_footer_present,
)


def test_valid_message(valid_message):
    print(valid_message)
    conv_commit = ConventionalCommit.from_message(valid_message["message"])
    assert conv_commit == valid_message["expected"]


def test_invalid_format(invalid_format_message):
    with pytest.raises(InvalidCommitMessageError):
        ConventionalCommit.from_message(invalid_format_message)


def test_invalid_type(invalid_type_message):
    with pytest.raises(InvalidCommitTypeError):
        ConventionalCommit.from_message(invalid_type_message)


def test_breaking_changes():
    message = """feat: add foo

This is a body

Closes: #123
BREAKING CHANGE: this is a first breaking change
multiline-footer: lorem
ipsum
dolor sit amet consectetur
A: 42
B #1234
C: 3
BREAKING-CHANGE: A second breaking change ends with a newline.

BREAKING CHANGE: A third breaking change contains a multiline paragraph below.

Lorem ipsum dolor: this is not a footer but a paragraph in a breaking change footer.

This is still a part of the third breaking change.
X: This is not a breaking change footer.
"""
    assert _breaking_change_footer_present(message)
