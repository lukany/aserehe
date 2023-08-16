import pytest

from aserehe._check import _check_single, InvalidCommitMessage, InvalidCommitType


def test_check_single(valid_message):
    _check_single(valid_message)


def test_invalid_format(invalid_format_message):
    with pytest.raises(InvalidCommitMessage):
        _check_single(invalid_format_message)


def test_invalid_type(invalid_type_message):
    with pytest.raises(InvalidCommitType):
        _check_single(invalid_type_message)
