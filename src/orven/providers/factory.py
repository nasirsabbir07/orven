from orven.config import ProviderSettings
from orven.providers.base import ModelProvider, ProviderError
from orven.providers.ollama import OllamaProvider


def create_provider(settings: ProviderSettings) -> ModelProvider:
    provider_name = settings.name.lower()
    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.base_url,
            model=settings.model,
            context_length=settings.context_length,
        )

    raise ProviderError(f"Unsupported provider '{settings.name}'. Supported providers: ollama.")
