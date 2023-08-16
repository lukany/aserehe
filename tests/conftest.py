import pytest


@pytest.fixture(
    params=(
        "chore: upgrade dependencies",
        "fix!: do not crash on empty input",
        "feat: add API endpoint",
        "test: add test",
        """chore!: drop support for Python 2

There is no reason to support Python 2 anymore.

BREAKING CHANGE: Python 2 is no longer supported
        """,
    ),
)
def valid_message(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(
    params=(
        "",
        "42",
        "chore upgrade dependencies",
        "feat(API) add endpoint",
        "docs: ",
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
