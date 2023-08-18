import pytest

from aserehe._check import (
    _check_single,
    InvalidCommitMessage,
    InvalidCommitType,
    _extract_breaking_change_footer_values,
)
from tests.conftest import ValidMessage


def test_check_single(valid_message: ValidMessage):
    conv_commit = _check_single(valid_message.message)
    assert conv_commit == valid_message.expected_conv_commit


def test_invalid_format(invalid_format_message):
    with pytest.raises(InvalidCommitMessage):
        _check_single(invalid_format_message)


def test_invalid_type(invalid_type_message):
    with pytest.raises(InvalidCommitType):
        _check_single(invalid_type_message)


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
    footers = _extract_breaking_change_footer_values(message)
    assert footers == [
        "this is a first breaking change",
        "A second breaking change ends with a newline.\n",
        """A third breaking change contains a multiline paragraph below.

Lorem ipsum dolor: this is not a footer but a paragraph in a breaking change footer.

This is still a part of the third breaking change.""",
    ]
