from orven.core import Agent, Conversation
from orven.providers import ModelInfo, ProviderRequest, ProviderResponse


class EchoProvider:
    name = "test"

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            text=f"echo: {request.prompt}",
            model="test-model",
            provider=self.name,
        )

    def list_models(self) -> list[ModelInfo]:
        return []


def test_agent_records_conversation_messages() -> None:
    conversation = Conversation()
    agent = Agent(EchoProvider(), conversation)

    response = agent.respond("hello")

    assert response == "echo: hello"
    assert [message.role for message in conversation.messages] == ["user", "assistant"]
    assert conversation.latest_user_prompt == "hello"
