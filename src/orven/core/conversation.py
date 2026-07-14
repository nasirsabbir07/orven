from typing import Literal

from pydantic import BaseModel, Field

MessageRole = Literal["user", "assistant"]


class Message(BaseModel):
    role: MessageRole
    content: str


class Conversation(BaseModel):
    messages: list[Message] = Field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(Message(role="assistant", content=content))

    @property
    def latest_user_prompt(self) -> str | None:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content

        return None
