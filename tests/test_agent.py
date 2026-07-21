from collections.abc import Callable
from pathlib import Path

import pytest

from orven.core import Agent
from orven.core.conversation import ToolCall, ToolCallFunction
from orven.core.tools import ToolRegistry, default_tools
from orven.core.tools.filesystem import ListDirTool
from orven.providers import ChatRequest, ChatResponse, Message, ProviderError


class ScriptedProvider:
    name = "test"

    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = iter(responses)

    def chat(
        self, request: ChatRequest, *, on_token: Callable[[str], None] | None = None
    ) -> ChatResponse:
        return next(self._responses)

    def list_models(self) -> list:  # pragma: no cover - unused in these tests
        return []


def _tool_call_response(name: str, arguments: dict) -> ChatResponse:
    return ChatResponse(
        message=Message(
            role="assistant",
            content="",
            tool_calls=[ToolCall(id="call_0", function=ToolCallFunction(name=name, arguments=arguments))],
        ),
        model="m",
        provider="test",
    )


def _final_text(content: str) -> ChatResponse:
    return ChatResponse(message=Message(role="assistant", content=content), model="m", provider="test")


def test_agent_executes_tool_call_and_resends_result(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("hello world")
    provider = ScriptedProvider(
        [_tool_call_response("read_file", {"path": "x.txt"}), _final_text("done")]
    )
    agent = Agent(provider, tools=ToolRegistry(default_tools()), root_dir=tmp_path)

    assert agent.respond("read the file") == "done"

    roles = [message.role for message in agent.conversation.messages]
    assert roles == ["system", "user", "assistant", "tool", "assistant"]
    tool_message = agent.conversation.messages[3]
    assert tool_message.tool_call_id == "call_0"
    assert "hello world" in tool_message.content


def test_agent_raises_after_max_iterations_without_executing_final_round(tmp_path: Path) -> None:
    always_tool_calls = _tool_call_response("list_dir", {"path": "."})
    provider = ScriptedProvider([always_tool_calls] * 8)

    calls: list[object] = []

    class SpyTool(ListDirTool):
        def run(self, args, context):
            calls.append(args)
            return super().run(args, context)

    agent = Agent(provider, tools=ToolRegistry([SpyTool()]), root_dir=tmp_path, max_iterations=8)

    with pytest.raises(ProviderError, match="tool-call loop"):
        agent.respond("loop forever")

    assert len(calls) == 7


def test_write_file_is_skipped_when_confirmation_declined(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("write_file", {"path": "a.txt", "content": "x"}), _final_text("ok")]
    )
    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        confirm=lambda _message: False,
        root_dir=tmp_path,
    )

    agent.respond("write a file")

    assert not (tmp_path / "a.txt").exists()
    tool_message = agent.conversation.messages[3]
    assert "declined" in tool_message.content


def test_write_file_executes_when_confirmed(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("write_file", {"path": "a.txt", "content": "x"}), _final_text("ok")]
    )
    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        confirm=lambda _message: True,
        root_dir=tmp_path,
    )

    agent.respond("write a file")

    assert (tmp_path / "a.txt").read_text() == "x"


def test_agent_reports_unknown_tool_without_crashing(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("does_not_exist", {}), _final_text("ok")]
    )
    agent = Agent(provider, tools=ToolRegistry(default_tools()), root_dir=tmp_path)

    assert agent.respond("call a missing tool") == "ok"
    tool_message = agent.conversation.messages[3]
    assert "unknown tool" in tool_message.content
