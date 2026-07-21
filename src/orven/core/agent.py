from collections.abc import Callable
from pathlib import Path

from orven.core.conversation import Conversation, ToolCall
from orven.core.tools import ConfirmFunc, ToolContext, ToolRegistry
from orven.providers import ChatRequest, ModelProvider, ProviderError

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
    ) -> None:
        self.provider = provider
        self.conversation = conversation or Conversation()
        self.tools = tools or ToolRegistry()
        self.confirm: ConfirmFunc = confirm or (lambda _message: False)
        self.root_dir = root_dir or Path.cwd()
        self.max_iterations = max_iterations
        if system_prompt:
            self.conversation.ensure_system_message(system_prompt)

    def respond(self, prompt: str, *, on_token: Callable[[str], None] | None = None) -> str:
        self.conversation.add_user_message(prompt)
        context = ToolContext(root_dir=self.root_dir)

        for iteration in range(self.max_iterations):
            request = ChatRequest(
                messages=self.conversation.history(),
                tools=self.tools.definitions(),
            )
            response = self.provider.chat(request, on_token=on_token)

            self.conversation.add_assistant_message(
                response.message.content, response.message.tool_calls
            )

            if not response.message.tool_calls:
                return response.message.content

            if iteration == self.max_iterations - 1:
                raise ProviderError(
                    f"Agent stopped after {self.max_iterations} tool-call iterations "
                    "without producing a final answer (possible tool-call loop)."
                )

            for tool_call in response.message.tool_calls:
                result_text = self._execute_tool_call(tool_call, context)
                self.conversation.add_tool_result(
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                    content=result_text,
                )

        raise AssertionError("unreachable")

    def _execute_tool_call(self, tool_call: ToolCall, context: ToolContext) -> str:
        tool = self.tools.get(tool_call.function.name)
        if tool is None:
            return f"Error: unknown tool '{tool_call.function.name}'."

        if tool.requires_confirmation:
            if not self.confirm(_describe_tool_call(tool_call)):
                return f"User declined to run '{tool.name}'."

        return tool.execute(tool_call.function.arguments, context).content


def _describe_tool_call(tool_call: ToolCall) -> str:
    args_preview = ", ".join(f"{key}={value!r}" for key, value in tool_call.function.arguments.items())
    return f"Run {tool_call.function.name}({args_preview})?"
