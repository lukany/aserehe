from typer.testing import CliRunner

from aserehe.__main__ import app
from tests.conftest import ValidMessage

runner = CliRunner()


def test_stdin(valid_message: ValidMessage):
    result = runner.invoke(app, ["check", "--from-stdin"], input=valid_message.message)
    assert result.exit_code == 0
