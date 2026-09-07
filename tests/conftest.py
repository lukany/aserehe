from pathlib import Path
from typing import Any, NamedTuple

import pytest
import yaml
from git.repo import Repo
from pytest import FixtureRequest, MonkeyPatch

from aserehe._commit import ConventionalCommit

_DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> Any:
    return yaml.safe_load((_DATA_DIR / filename).read_text())


def _summary(message: str) -> str:
    return message.splitlines()[0] if message else "<empty>"


class ValidMessage(NamedTuple):
    message: str
    expected: ConventionalCommit


@pytest.fixture(
    params=_load("valid_messages.yaml"), ids=lambda case: _summary(case["message"])
)
def valid_message(request: FixtureRequest) -> ValidMessage:
    case = request.param
    return ValidMessage(
        message=case["message"],
        expected=ConventionalCommit(type=case["type"], breaking=case["breaking"]),
    )


@pytest.fixture(params=_load("invalid_format_messages.yaml"), ids=_summary)
def invalid_format_message(request: FixtureRequest) -> str:
    message: str = request.param
    return message


@pytest.fixture(params=_load("invalid_type_messages.yaml"), ids=_summary)
def invalid_type_message(request: FixtureRequest) -> str:
    message: str = request.param
    return message


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: MonkeyPatch) -> Repo:
    """An empty git repository that is also the current working directory."""
    repo = Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "test")
        config.set_value("user", "email", "test@example.com")
    monkeypatch.chdir(tmp_path)
    return repo
