from orven.core.conversation import Conversation
from orven.providers import ModelProvider, ProviderRequest


class Agent:
    def __init__(
        self,
        provider: ModelProvider,
        conversation: Conversation | None = None,
    ) -> None:
        self.provider = provider
        self.conversation = conversation or Conversation()

    def respond(self, prompt: str) -> str:
        self.conversation.add_user_message(prompt)
        response = self.provider.complete(ProviderRequest(prompt=prompt))
        self.conversation.add_assistant_message(response.text)
        return response.text
