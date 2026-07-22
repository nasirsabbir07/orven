import json
from collections.abc import Callable
from pathlib import Path

from orven.core.conversation import Conversation, ToolCall
from orven.core.skills import Skill, format_skill_catalog
from orven.core.tools import ConfirmFunc, LoadSkillTool, ToolContext, ToolRegistry
from orven.core.trace import StopReason, ToolCallRequest, ToolInvocationRecord, TurnRecord
from orven.providers import ChatRequest, ModelProvider, ProviderError

OnTurnFunc = Callable[[TurnRecord], None]

DEFAULT_SYSTEM_PROMPT = (
    "You are Orven, a local coding assistant running against a local model. "
    "You have access to tools for reading files, listing directories, and writing files. "
    "Use tools when they would help answer the user accurately; do not guess about file contents."
)
DEFAULT_MAX_ITERATIONS = 8


class Agent:
    def __init__(
        self,
        provider: ModelProvider,
        conversation: Conversation | None = None,
        *,
        tools: ToolRegistry | None = None,
        confirm: ConfirmFunc | None = None,
        root_dir: Path | None = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        system_prompt: str | None = DEFAULT_SYSTEM_PROMPT,
        skills: list[Skill] | None = None,
        on_turn: OnTurnFunc | None = None,
    ) -> None:
        self.provider = provider
        self.conversation = conversation or Conversation()
        self.tools = tools or ToolRegistry()
        self.confirm: ConfirmFunc = confirm or (lambda _message: False)
        self.root_dir = root_dir or Path.cwd()
        self.max_iterations = max_iterations
        self.on_turn = on_turn
        self.skills = list(skills or [])
        if self.skills:
            self.tools.register(LoadSkillTool(self.skills))

        if system_prompt and self.skills:
            system_prompt = f"{system_prompt}\n\n{format_skill_catalog(self.skills)}"
        if system_prompt:
            self.conversation.ensure_system_message(system_prompt)

    def respond(self, prompt: str, *, on_token: Callable[[str], None] | None = None) -> str:
        self.conversation.add_user_message(prompt)
        context = ToolContext(root_dir=self.root_dir)
        previous_signature: tuple[tuple[str, str], ...] | None = None

        for iteration in range(self.max_iterations):
            prior_message_count = len(self.conversation.messages)
            request = ChatRequest(
                messages=self.conversation.history(),
                tools=self.tools.definitions(),
            )
            response = self.provider.chat(request, on_token=on_token)

            self.conversation.add_assistant_message(
                response.message.content, response.message.tool_calls
            )

            requested_tool_calls = [
                ToolCallRequest(
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                for tool_call in response.message.tool_calls or []
            ]

            if not response.message.tool_calls:
                self._emit_turn(
                    iteration=iteration,
                    prior_message_count=prior_message_count,
                    assistant_content=response.message.content,
                    requested_tool_calls=requested_tool_calls,
                    tool_invocations=[],
                    stop_reason="final_answer",
                )
                return response.message.content

            signature = _tool_call_signature(response.message.tool_calls)
            if signature == previous_signature:
                self._emit_turn(
                    iteration=iteration,
                    prior_message_count=prior_message_count,
                    assistant_content=response.message.content,
                    requested_tool_calls=requested_tool_calls,
                    tool_invocations=[],
                    stop_reason="stagnant_loop",
                )
                raise ProviderError(
                    "Agent stopped: the model repeated an identical tool call with no "
                    "new evidence between iterations (stagnant tool-call loop)."
                )
            previous_signature = signature

            if iteration == self.max_iterations - 1:
                self._emit_turn(
                    iteration=iteration,
                    prior_message_count=prior_message_count,
                    assistant_content=response.message.content,
                    requested_tool_calls=requested_tool_calls,
                    tool_invocations=[],
                    stop_reason="max_iterations",
                )
                raise ProviderError(
                    f"Agent stopped after {self.max_iterations} tool-call iterations "
                    "without producing a final answer (possible tool-call loop)."
                )

            tool_invocations = []
            for tool_call in response.message.tool_calls:
                result_text, ok = self._execute_tool_call(tool_call, context)
                self.conversation.add_tool_result(
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                    content=result_text,
                )
                tool_invocations.append(
                    ToolInvocationRecord(
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        result=result_text,
                        ok=ok,
                    )
                )

            self._emit_turn(
                iteration=iteration,
                prior_message_count=prior_message_count,
                assistant_content=response.message.content,
                requested_tool_calls=requested_tool_calls,
                tool_invocations=tool_invocations,
                stop_reason="continue",
            )

        raise AssertionError("unreachable")

    def _emit_turn(
        self,
        *,
        iteration: int,
        prior_message_count: int,
        assistant_content: str,
        requested_tool_calls: list[ToolCallRequest],
        tool_invocations: list[ToolInvocationRecord],
        stop_reason: StopReason,
    ) -> None:
        if self.on_turn is None:
            return

        self.on_turn(
            TurnRecord(
                iteration=iteration,
                prior_message_count=prior_message_count,
                assistant_content=assistant_content,
                requested_tool_calls=requested_tool_calls,
                tool_invocations=tool_invocations,
                stop_reason=stop_reason,
            )
        )

    def _execute_tool_call(self, tool_call: ToolCall, context: ToolContext) -> tuple[str, bool]:
        tool = self.tools.get(tool_call.function.name)
        if tool is None:
            return f"Error: unknown tool '{tool_call.function.name}'.", False

        if tool.requires_confirmation:
            try:
                confirmed = self.confirm(_describe_tool_call(tool_call))
            except Exception as error:
                return f"Error: confirmation for '{tool.name}' failed: {error}", False

            if not confirmed:
                return f"User declined to run '{tool.name}'.", True

        try:
            result = tool.execute(tool_call.function.arguments, context)
            return result.content, result.ok
        except Exception as error:
            return f"Error: '{tool.name}' raised an unexpected error: {error}", False


def _describe_tool_call(tool_call: ToolCall) -> str:
    args_preview = ", ".join(f"{key}={value!r}" for key, value in tool_call.function.arguments.items())
    return f"Run {tool_call.function.name}({args_preview})?"


def _tool_call_signature(tool_calls: list[ToolCall]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (tool_call.function.name, json.dumps(tool_call.function.arguments, sort_keys=True, default=str))
        for tool_call in tool_calls
    )
