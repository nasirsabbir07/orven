from typer.testing import CliRunner

from orven.main import app

runner = CliRunner()


def test_root_command_starts_orven() -> None:
    result = runner.invoke(app, input="/exit\n")

    assert result.exit_code == 0
    assert "Orven" in result.output
    assert "orven" in result.output
    assert "Exiting Orven." in result.output


def test_root_command_accepts_agent_tasks() -> None:
    result = runner.invoke(app, input="summarize this repo\n/exit\n")

    assert result.exit_code == 0
    assert "no model provider is configured yet" in result.output


def test_root_command_shows_slash_help() -> None:
    result = runner.invoke(app, input="/help\n/exit\n")

    assert result.exit_code == 0
    assert "/help" in result.output
    assert "/exit" in result.output


def test_hello_command() -> None:
    result = runner.invoke(app, ["hello"])

    assert result.exit_code == 0
    assert "Hello from Orven!" in result.output


def test_help_lists_hello_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "hello" in result.output


def test_exit_command() -> None:
    result = runner.invoke(app, ["exit"])

    assert result.exit_code == 0
    assert "Exiting Orven." in result.output
