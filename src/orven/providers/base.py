from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant", "tool"]


class ToolCallFunction(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    id: str
    function: ToolCallFunction


class Message(BaseModel):
    role: MessageRole
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ProviderError(Exception):
    """Raised when a model provider cannot complete a request."""


class ToolsNotSupportedError(ProviderError):
    """Raised when the configured model rejects tool/function-calling."""


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_function(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ChatRequest(BaseModel):
    messages: list[Message]
    tools: list[ToolDefinition] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: Message
    model: str
    provider: str

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.message.tool_calls)


class ModelInfo(BaseModel):
    name: str


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def chat(
        self,
        request: ChatRequest,
        *,
        on_token: Callable[[str], None] | None = None,
    ) -> ChatResponse:
        """Return a chat completion, optionally requesting tool calls."""

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Return models available to this provider."""
