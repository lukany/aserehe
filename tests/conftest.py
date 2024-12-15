from pathlib import Path

import pytest
import yaml

from aserehe._commit import ConventionalCommit


def load_yaml_data(filename: str) -> list:
    data_dir = Path(__file__).parent / "data"
    with open(data_dir / filename, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(params=load_yaml_data("valid_messages.yaml"))
def valid_message(request):
    data = request.param
    return {
        "message": data["message"],
        "expected": ConventionalCommit(type=data["type"], breaking=data["breaking"]),
    }


@pytest.fixture(params=load_yaml_data("invalid_format_messages.yaml"))
def invalid_format_message(request):
    return request.param


@pytest.fixture(params=load_yaml_data("invalid_type_messages.yaml"))
def invalid_type_message(request):
    return request.param
