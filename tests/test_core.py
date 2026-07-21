from collections.abc import Callable

from orven.core import Agent, Conversation
from orven.providers import ChatRequest, ChatResponse, Message, ModelInfo


class EchoProvider:
    name = "test"

    def chat(
        self, request: ChatRequest, *, on_token: Callable[[str], None] | None = None
    ) -> ChatResponse:
        prompt = request.messages[-1].content
        return ChatResponse(
            message=Message(role="assistant", content=f"echo: {prompt}"),
            model="test-model",
            provider=self.name,
        )

    def list_models(self) -> list[ModelInfo]:
        return []


def test_agent_records_conversation_messages() -> None:
    conversation = Conversation()
    agent = Agent(EchoProvider(), conversation, system_prompt=None)

    response = agent.respond("hello")

    assert response == "echo: hello"
    assert [message.role for message in conversation.messages] == ["user", "assistant"]
    assert conversation.latest_user_prompt == "hello"


def test_agent_injects_system_prompt_by_default() -> None:
    conversation = Conversation()
    agent = Agent(EchoProvider(), conversation)

    agent.respond("hello")

    assert [message.role for message in conversation.messages] == ["system", "user", "assistant"]
