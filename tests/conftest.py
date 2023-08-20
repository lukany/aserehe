from dataclasses import dataclass

import pytest

from aserehe._check import ConventionalCommit


@dataclass
class ValidMessage:
    message: str
    expected_conv_commit: ConventionalCommit


@pytest.fixture(
    params=(
        ValidMessage(
            message="chore: upgrade dependencies",
            expected_conv_commit=ConventionalCommit(type="chore", breaking=False),
        ),
        ValidMessage(
            message="fix!: do not crash on empty input",
            expected_conv_commit=ConventionalCommit(type="fix", breaking=True),
        ),
        ValidMessage(
            message="feat: add API endpoint",
            expected_conv_commit=ConventionalCommit(type="feat", breaking=False),
        ),
        ValidMessage(
            message="test: add test",
            expected_conv_commit=ConventionalCommit(type="test", breaking=False),
        ),
        ValidMessage(
            message="""chore!: drop support for Python 2

There is no reason to support Python 2 anymore.

BREAKING CHANGE: Python 2 is no longer supported
        """,
            expected_conv_commit=ConventionalCommit(type="chore", breaking=True),
        ),
        ValidMessage(
            message="""fix: do not crash on empty input


Message body
""",
            expected_conv_commit=ConventionalCommit(type="fix", breaking=False),
        ),
        ValidMessage(
            message="""fix: delete invalid modules

BREAKING-CHANGE: module X is not longer available""",
            expected_conv_commit=ConventionalCommit(type="fix", breaking=True),
        ),
    ),
)
def valid_message(request: pytest.FixtureRequest) -> ValidMessage:
    return request.param


@pytest.fixture(
    params=(
        "",
        "42",
        "chore upgrade dependencies",
        "feat(API) add endpoint",
        "docs: ",
        """fix: do not crash on empty input
this line should be empty""",
    ),
)
def invalid_format_message(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(
    params=(
        "42: the answer",
        "tests: add test",
        "doc: add documentation",
        "feature: add API endpoint",
    ),
)
def invalid_type_message(request: pytest.FixtureRequest) -> str:
    return request.param
