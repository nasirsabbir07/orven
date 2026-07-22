from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from orven.cli import shell
from orven.cli.commands import doctor, general, model, skills
from orven.config import load_config
from orven.main import app
from orven.providers import (
    ChatRequest,
    ChatResponse,
    Message,
    ModelInfo,
    ProviderError,
    ToolCall,
    ToolCallFunction,
)

runner = CliRunner()


class FailingProvider:
    name = "test"

    def chat(
        self, request: ChatRequest, *, on_token: Callable[[str], None] | None = None
    ) -> ChatResponse:
        raise ProviderError("provider unavailable")

    def list_models(self) -> list[ModelInfo]:
        return []


class ModelListProvider:
    name = "test"

    def chat(
        self, request: ChatRequest, *, on_token: Callable[[str], None] | None = None
    ) -> ChatResponse:
        if on_token is not None:
            on_token("ok")
        return ChatResponse(
            message=Message(role="assistant", content="ok"), model="llama3:8b", provider=self.name
        )

    def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(name="llama3:8b"), ModelInfo(name="gemma4:26b")]


def test_root_command_starts_interactive_shell() -> None:
    result = runner.invoke(app, input="/exit\n")

    assert result.exit_code == 0
    assert "Orven" in result.output
    assert "orven" in result.output
    assert "Exiting Orven." in result.output


def test_root_command_accepts_agent_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell, "create_provider", lambda _: ModelListProvider())

    result = runner.invoke(app, input="summarize this repo\n/exit\n")

    assert result.exit_code == 0
    assert "ok" in result.output


def test_root_command_shows_slash_help() -> None:
    result = runner.invoke(app, input="/help\n/exit\n")

    assert result.exit_code == 0
    assert "/help" in result.output
    assert "/config" in result.output
    assert "/exit" in result.output
    assert "/provider" in result.output
    assert "/providers" in result.output
    assert "/skills" in result.output
    assert "/skill" in result.output


def test_root_command_shows_config() -> None:
    result = runner.invoke(app, input="/config\n/exit\n")

    assert result.exit_code == 0
    assert "Config path:" in result.output
    assert "Provider: ollama" in result.output


def test_root_command_lists_providers() -> None:
    result = runner.invoke(app, input="/providers\n/exit\n")

    assert result.exit_code == 0
    assert "1. ollama *" in result.output


def test_root_command_selects_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(shell, "load_config", lambda: load_config(config_path))

    result = runner.invoke(app, input="/provider\n1\n/exit\n")

    assert result.exit_code == 0
    assert "Selected provider: ollama" in result.output


def test_root_command_lists_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell, "create_provider", lambda _: ModelListProvider())

    result = runner.invoke(app, input="/models\n/exit\n")

    assert result.exit_code == 0
    assert "1. llama3:8b" in result.output
    assert "2. gemma4:26b" in result.output


def test_root_command_selects_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(shell, "create_provider", lambda _: ModelListProvider())
    monkeypatch.setattr(shell, "load_config", lambda: load_config(config_path))

    result = runner.invoke(app, input="/model\n2\n/exit\n")

    assert result.exit_code == 0
    assert "Selected model: gemma4:26b" in result.output


def test_root_command_lists_skills(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "code-review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(["---", "name: code-review", "description: Reviews code.", "---", "Check bugs."]),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(shell, "load_config", lambda: load_config(config_path))
    monkeypatch.setenv("ORVEN_SKILLS_DIR", str(skills_dir))

    result = runner.invoke(app, input="/skills\n/exit\n")

    assert result.exit_code == 0
    assert "code-review: Reviews code." in result.output


def test_root_command_shows_skill(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "code-review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(["---", "name: code-review", "description: Reviews code.", "---", "Check bugs."]),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(shell, "load_config", lambda: load_config(config_path))
    monkeypatch.setenv("ORVEN_SKILLS_DIR", str(skills_dir))

    result = runner.invoke(app, input="/skill\ncode-review\n/exit\n")

    assert result.exit_code == 0
    assert "Check bugs." in result.output


def test_run_command_starts_interactive_shell() -> None:
    result = runner.invoke(app, ["run"], input="/exit\n")

    assert result.exit_code == 0
    assert "Type a task, or /help for commands." in result.output


def test_chat_command_starts_interactive_shell() -> None:
    result = runner.invoke(app, ["chat"], input="/exit\n")

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
    assert "chat" in result.output
    assert "ask" in result.output
    assert "hello" in result.output
    assert "exit" in result.output
    assert "providers" in result.output
    assert "model" in result.output
    assert "skills" in result.output
    assert "workflows" in result.output
    assert "doctor" in result.output
    assert "config" in result.output


def test_exit_command() -> None:
    result = runner.invoke(app, ["exit"])

    assert result.exit_code == 0
    assert "Exiting Orven." in result.output


def test_provider_skill_and_workflow_list_commands() -> None:
    provider_result = runner.invoke(app, ["providers", "list"])
    skill_result = runner.invoke(app, ["skills", "list"])
    workflow_result = runner.invoke(app, ["workflows", "list"])

    assert provider_result.exit_code == 0
    assert "Configured provider: ollama" in provider_result.output
    assert skill_result.exit_code == 0
    assert "No local skills" in skill_result.output
    assert workflow_result.exit_code == 0
    assert "No local workflows" in workflow_result.output


def test_skills_list_and_show_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "code-review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: code-review",
                "description: Reviews code for bugs.",
                "---",
                "Check for edge cases and off-by-one errors.",
            ]
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(skills, "load_config", lambda: load_config(config_path))
    monkeypatch.setenv("ORVEN_SKILLS_DIR", str(skills_dir))

    list_result = runner.invoke(app, ["skills", "list"])
    show_result = runner.invoke(app, ["skills", "show", "code-review"])
    missing_result = runner.invoke(app, ["skills", "show", "does-not-exist"])

    assert list_result.exit_code == 0
    assert "code-review: Reviews code for bugs." in list_result.output
    assert show_result.exit_code == 0
    assert "Check for edge cases and off-by-one errors." in show_result.output
    assert missing_result.exit_code == 1


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Provider runtime:" in result.output


def test_doctor_command_reports_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_provider_error(_):
        raise ProviderError("provider unavailable")

    monkeypatch.setattr(doctor, "create_provider", raise_provider_error)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Provider runtime: not ready" in result.output


def test_config_command_shows_resolved_config() -> None:
    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert "Config path:" in result.output
    assert "Provider: ollama" in result.output


def test_ask_command_reports_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(general, "create_provider", lambda _: FailingProvider())

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "provider unavailable" in result.output


class ToolCallThenDoneProvider:
    name = "test"

    def __init__(self) -> None:
        self._responses = iter(
            [
                ChatResponse(
                    message=Message(
                        role="assistant",
                        content="",
                        tool_calls=[
                            ToolCall(
                                id="call_0",
                                function=ToolCallFunction(name="list_dir", arguments={"path": "."}),
                            )
                        ],
                    ),
                    model="test-model",
                    provider="test",
                ),
                ChatResponse(message=Message(role="assistant", content="done"), model="test-model", provider="test"),
            ]
        )

    def chat(
        self, request: ChatRequest, *, on_token: Callable[[str], None] | None = None
    ) -> ChatResponse:
        response = next(self._responses)
        if on_token is not None and response.message.content:
            on_token(response.message.content)
        return response

    def list_models(self) -> list[ModelInfo]:
        return []


def test_ask_command_prints_turn_receipts_when_verbose(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(general, "create_provider", lambda _: ToolCallThenDoneProvider())

    result = runner.invoke(app, ["ask", "list the directory", "--verbose"])

    assert result.exit_code == 0
    assert "[turn 0] list_dir(path='.') -> ok:" in result.output


def test_ask_command_is_quiet_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(general, "create_provider", lambda _: ToolCallThenDoneProvider())

    result = runner.invoke(app, ["ask", "list the directory"])

    assert result.exit_code == 0
    assert "[turn" not in result.output


def test_model_list_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model, "create_provider", lambda _: ModelListProvider())

    result = runner.invoke(app, ["model", "list"])

    assert result.exit_code == 0
    assert "llama3:8b" in result.output
    assert "gemma4:26b" in result.output


def test_model_set_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(model, "create_provider", lambda _: ModelListProvider())
    monkeypatch.setattr(model, "load_config", lambda: load_config(config_path))

    result = runner.invoke(app, ["model", "set", "llama3:8b"])

    assert result.exit_code == 0
    assert "Selected model: llama3:8b" in result.output
