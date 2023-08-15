import typer

from aserehe.check import _check_git, _check_single

app = typer.Typer()


@app.command()
def check(from_stdin: bool = typer.Option(False, "--from-stdin")):
    if from_stdin:
        stdin = typer.get_text_stream("stdin")
        _check_single(stdin.read())
    else:
        _check_git()


if __name__ == "__main__":
    app()
