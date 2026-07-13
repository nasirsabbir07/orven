from typer.testing import CliRunner

from orven.main import app

runner = CliRunner()


def test_root_command_starts_interactive_shell() -> None:
    result = runner.invoke(app, input="/exit\n")

    assert result.exit_code == 0
    assert "Orven" in result.output
    assert "orven" in result.output
    assert "Exiting Orven." in result.output


def test_run_command_starts_interactive_shell() -> None:
    result = runner.invoke(app, ["run"], input="/exit\n")

    assert result.exit_code == 0
    assert "Type a task, or /help for commands." in result.output


def test_hello_command() -> None:
    result = runner.invoke(app, ["hello"])

    assert result.exit_code == 0
    assert "Hello from Orven!" in result.output


def test_help_lists_command_tree() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "run" in result.output
    assert "providers" in result.output
    assert "skills" in result.output
    assert "workflows" in result.output
    assert "doctor" in result.output


def test_provider_skill_and_workflow_list_commands() -> None:
    provider_result = runner.invoke(app, ["providers", "list"])
    skill_result = runner.invoke(app, ["skills", "list"])
    workflow_result = runner.invoke(app, ["workflows", "list"])

    assert provider_result.exit_code == 0
    assert "No model providers" in provider_result.output
    assert skill_result.exit_code == 0
    assert "No local skills" in skill_result.output
    assert workflow_result.exit_code == 0
    assert "No local workflows" in workflow_result.output


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Provider runtime: not configured" in result.output
