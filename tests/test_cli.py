from typer.testing import CliRunner

from aserehe.__main__ import app

runner = CliRunner()


def test_stdin(valid_message):
    result = runner.invoke(app, ["--from-stdin"], input=valid_message)
    assert result.exit_code == 0
