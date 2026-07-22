from collections.abc import Callable
from pathlib import Path

import pytest

from orven.core import Agent, TurnRecord
from orven.core.conversation import ToolCall, ToolCallFunction
from orven.core.skills import Skill
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
    varying_tool_calls = [_tool_call_response("list_dir", {"path": str(i)}) for i in range(8)]
    provider = ScriptedProvider(varying_tool_calls)

    calls: list[object] = []

    class SpyTool(ListDirTool):
        def run(self, args, context):
            calls.append(args)
            return super().run(args, context)

    agent = Agent(provider, tools=ToolRegistry([SpyTool()]), root_dir=tmp_path, max_iterations=8)

    with pytest.raises(ProviderError, match="possible tool-call loop"):
        agent.respond("loop forever")

    assert len(calls) == 7


def test_agent_detects_stagnant_tool_call_loop(tmp_path: Path) -> None:
    identical_tool_calls = _tool_call_response("list_dir", {"path": "."})
    provider = ScriptedProvider([identical_tool_calls] * 8)

    calls: list[object] = []

    class SpyTool(ListDirTool):
        def run(self, args, context):
            calls.append(args)
            return super().run(args, context)

    agent = Agent(provider, tools=ToolRegistry([SpyTool()]), root_dir=tmp_path, max_iterations=8)

    with pytest.raises(ProviderError, match="stagnant tool-call loop"):
        agent.respond("repeat the same call forever")

    assert len(calls) == 1


def test_agent_converts_unexpected_tool_error_into_tool_result(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("list_dir", {"path": "."}), _final_text("done")]
    )

    class ExplodingTool(ListDirTool):
        def run(self, args, context):
            raise RuntimeError("disk on fire")

    agent = Agent(provider, tools=ToolRegistry([ExplodingTool()]), root_dir=tmp_path)

    assert agent.respond("list a directory") == "done"

    roles = [message.role for message in agent.conversation.messages]
    assert roles == ["system", "user", "assistant", "tool", "assistant"]
    tool_message = agent.conversation.messages[3]
    assert "unexpected error" in tool_message.content
    assert "disk on fire" in tool_message.content


def test_agent_converts_confirmation_error_into_tool_result(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("write_file", {"path": "a.txt", "content": "x"}), _final_text("done")]
    )

    def _broken_confirm(_message: str) -> bool:
        raise RuntimeError("prompt backend unavailable")

    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        confirm=_broken_confirm,
        root_dir=tmp_path,
    )

    assert agent.respond("write a file") == "done"

    assert not (tmp_path / "a.txt").exists()
    tool_message = agent.conversation.messages[3]
    assert "confirmation" in tool_message.content
    assert "prompt backend unavailable" in tool_message.content


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


def test_agent_emits_turn_receipts_for_tool_call_and_final_answer(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("hello world")
    provider = ScriptedProvider(
        [_tool_call_response("read_file", {"path": "x.txt"}), _final_text("done")]
    )
    receipts: list[TurnRecord] = []
    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        root_dir=tmp_path,
        on_turn=receipts.append,
    )

    agent.respond("read the file")

    assert [receipt.stop_reason for receipt in receipts] == ["continue", "final_answer"]

    first = receipts[0]
    assert first.requested_tool_calls[0].name == "read_file"
    assert first.tool_invocations[0].ok is True
    assert "hello world" in first.tool_invocations[0].result

    assert receipts[1].requested_tool_calls == []
    assert receipts[1].tool_invocations == []


def test_agent_emits_receipt_before_raising_on_stagnant_loop(tmp_path: Path) -> None:
    identical_tool_calls = _tool_call_response("list_dir", {"path": "."})
    provider = ScriptedProvider([identical_tool_calls] * 8)
    receipts: list[TurnRecord] = []
    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        root_dir=tmp_path,
        max_iterations=8,
        on_turn=receipts.append,
    )

    with pytest.raises(ProviderError, match="stagnant tool-call loop"):
        agent.respond("repeat the same call forever")

    assert [receipt.stop_reason for receipt in receipts] == ["continue", "stagnant_loop"]
    assert receipts[-1].requested_tool_calls[0].name == "list_dir"
    assert receipts[-1].tool_invocations == []


def test_agent_injects_skill_catalog_and_loads_skill_on_demand(tmp_path: Path) -> None:
    skill = Skill(
        name="code-review",
        description="Reviews code for bugs.",
        body="Check for edge cases and off-by-one errors.",
        path=tmp_path / "SKILL.md",
    )
    provider = ScriptedProvider(
        [_tool_call_response("load_skill", {"name": "code-review"}), _final_text("done")]
    )
    agent = Agent(provider, tools=ToolRegistry(default_tools()), root_dir=tmp_path, skills=[skill])

    assert agent.respond("review this code") == "done"

    system_message = agent.conversation.messages[0]
    assert "code-review: Reviews code for bugs." in system_message.content

    tool_message = agent.conversation.messages[3]
    assert tool_message.content == "Check for edge cases and off-by-one errors."


def test_agent_reports_unknown_skill_name_without_crashing(tmp_path: Path) -> None:
    skill = Skill(name="code-review", description="d", body="b", path=tmp_path / "SKILL.md")
    provider = ScriptedProvider(
        [_tool_call_response("load_skill", {"name": "does-not-exist"}), _final_text("done")]
    )
    agent = Agent(provider, tools=ToolRegistry(default_tools()), root_dir=tmp_path, skills=[skill])

    assert agent.respond("review this code") == "done"

    tool_message = agent.conversation.messages[3]
    assert "Unknown skill" in tool_message.content
    assert "code-review" in tool_message.content


def test_agent_receipt_marks_unknown_tool_invocation_as_not_ok(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        [_tool_call_response("does_not_exist", {}), _final_text("ok")]
    )
    receipts: list[TurnRecord] = []
    agent = Agent(
        provider,
        tools=ToolRegistry(default_tools()),
        root_dir=tmp_path,
        on_turn=receipts.append,
    )

    agent.respond("call a missing tool")

    assert receipts[0].tool_invocations[0].ok is False
