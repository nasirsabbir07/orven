from pydantic import BaseModel, Field

from orven.providers.base import Message, MessageRole, ToolCall, ToolCallFunction

__all__ = ["Conversation", "Message", "MessageRole", "ToolCall", "ToolCallFunction"]


class Conversation(BaseModel):
    messages: list[Message] = Field(default_factory=list)

    def ensure_system_message(self, content: str) -> None:
        if self.messages and self.messages[0].role == "system":
            self.messages[0] = Message(role="system", content=content)
        else:
            self.messages.insert(0, Message(role="system", content=content))

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(
        self, content: str, tool_calls: list[ToolCall] | None = None
    ) -> None:
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )

    def add_tool_result(self, *, tool_call_id: str, name: str, content: str) -> None:
        self.messages.append(
            Message(role="tool", tool_call_id=tool_call_id, name=name, content=content)
        )

    def history(self) -> list[Message]:
        return list(self.messages)

    @property
    def latest_user_prompt(self) -> str | None:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content

        return None
