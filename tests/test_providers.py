import httpx
import pytest

from orven.config import ProviderSettings
from orven.providers import (
    OllamaProvider,
    ProviderError,
    ProviderRequest,
    create_provider,
)


def test_ollama_provider_sends_generate_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == "http://ollama.test/api/generate"
        assert request.read() == (
            b'{"model":"llama3.2","prompt":"hello","stream":false}'
        )
        return httpx.Response(200, json={"response": "Hello from Ollama", "model": "llama3.2"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.2", client=client)

    response = provider.complete(ProviderRequest(prompt="hello"))

    assert response.text == "Hello from Ollama"
    assert response.model == "llama3.2"
    assert response.provider == "ollama"


def test_ollama_provider_uses_first_local_model_when_unconfigured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2"}]})

        assert request.url.path == "/api/generate"
        assert b'"model":"llama3.2"' in request.read()
        return httpx.Response(200, json={"response": "Hello", "model": "llama3.2"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", client=client)

    response = provider.complete(ProviderRequest(prompt="hello"))

    assert response.text == "Hello"
    assert response.model == "llama3.2"


def test_ollama_provider_lists_local_models() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"models": [{"name": "llama3.2"}, {"name": "qwen2.5-coder"}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", client=client)

    assert [model.name for model in provider.list_models()] == ["llama3.2", "qwen2.5-coder"]


def test_ollama_provider_errors_when_no_local_models_exist() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", client=client)

    with pytest.raises(ProviderError, match="No Ollama models are installed"):
        provider.complete(ProviderRequest(prompt="hello"))


def test_ollama_provider_reports_missing_model() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="missing", client=client)

    with pytest.raises(ProviderError, match="model not found"):
        provider.complete(ProviderRequest(prompt="hello"))


def test_ollama_provider_reports_connection_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.2", client=client)

    with pytest.raises(ProviderError, match="Could not connect to Ollama"):
        provider.complete(ProviderRequest(prompt="hello"))


def test_create_provider_allows_ollama_without_configured_model() -> None:
    settings = ProviderSettings(name="ollama", model=None)

    provider = create_provider(settings)

    assert isinstance(provider, OllamaProvider)


def test_create_provider_rejects_unsupported_provider() -> None:
    settings = ProviderSettings(name="vllm", model="qwen")

    with pytest.raises(ProviderError, match="Unsupported provider"):
        create_provider(settings)
