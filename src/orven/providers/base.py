from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProviderError(Exception):
    """Raised when a model provider cannot complete a request."""


class ProviderRequest(BaseModel):
    prompt: str


class ProviderResponse(BaseModel):
    text: str
    model: str
    provider: str


class ModelInfo(BaseModel):
    name: str


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Return a completion for a prompt."""

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Return models available to this provider."""
