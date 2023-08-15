import pytest

from aserehe.check import _check_single, InvalidCommitMessage, InvalidCommitType


@pytest.mark.parametrize(
    "message",
    (
        "chore: upgrade dependencies",
        "fix!: do not crash on empty input",
        "feat: add API endpoint",
        "test: add test",
    ),
)
def test_check_single(message):
    _check_single(message)


@pytest.mark.parametrize(
    "message",
    ("", "42", "chore upgrade dependencies", "feat(API) add endpoint", "docs: "),
)
def test_invalid_format(message):
    with pytest.raises(InvalidCommitMessage):
        _check_single(message)


@pytest.mark.parametrize(
    "message",
    (
        "42: the answer",
        "tests: add test",
        "doc: add documentation",
        "feature: add API endpoint",
    ),
)
def test_invalid_type(message):
    with pytest.raises(InvalidCommitType):
        _check_single(message)
