import httpx
import pytest

from orven.config import ProviderSettings
from orven.providers import (
    ChatRequest,
    Message,
    OllamaProvider,
    ProviderError,
    ToolDefinition,
    ToolsNotSupportedError,
    create_provider,
)


def test_ollama_provider_sends_chat_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == "http://ollama.test/api/chat"
        assert request.read() == (
            b'{"model":"llama3.2","messages":[{"role":"user","content":"hello"}],'
            b'"stream":false}'
        )
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "Hello from Ollama"}, "model": "llama3.2"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.2", client=client)

    response = provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))

    assert response.message.content == "Hello from Ollama"
    assert response.model == "llama3.2"
    assert response.provider == "ollama"
    assert response.has_tool_calls is False


def test_ollama_provider_sends_num_ctx_when_context_length_configured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"options":{"num_ctx":8192}' in request.read()
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "ok"}, "model": "llama3.2"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(
        base_url="http://ollama.test", model="llama3.2", context_length=8192, client=client
    )

    provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))


def test_ollama_provider_omits_options_when_context_length_unset() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"options"' not in request.read()
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "ok"}, "model": "llama3.2"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.2", client=client)

    provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))


def test_ollama_provider_uses_first_local_model_when_unconfigured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2"}]})

        assert request.url.path == "/api/chat"
        assert b'"model":"llama3.2"' in request.read()
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "Hello"}, "model": "llama3.2"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", client=client)

    response = provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))

    assert response.message.content == "Hello"
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
        provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))


def test_ollama_provider_reports_missing_model() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="missing", client=client)

    with pytest.raises(ProviderError, match="model not found"):
        provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))


def test_ollama_provider_reports_connection_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.2", client=client)

    with pytest.raises(ProviderError, match="Could not connect to Ollama"):
        provider.chat(ChatRequest(messages=[Message(role="user", content="hello")]))


def test_ollama_provider_streams_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream":true' in request.read()
        lines = (
            b'{"message":{"role":"assistant","content":"Hel"},"done":false}\n'
            b'{"message":{"role":"assistant","content":"lo"},"done":false}\n'
            b'{"message":{"role":"assistant","content":""},"done":true,"model":"llama3.1"}\n'
        )
        return httpx.Response(200, content=lines)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama3.1", client=client)

    tokens: list[str] = []
    response = provider.chat(
        ChatRequest(messages=[Message(role="user", content="hi")]),
        on_token=tokens.append,
    )

    assert tokens == ["Hel", "lo"]
    assert response.message.content == "Hello"
    assert response.model == "llama3.1"


def test_ollama_provider_parses_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"tools"' in request.read()
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "read_file", "arguments": {"path": "a.txt"}}}
                    ],
                },
                "model": "qwen2.5",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="qwen2.5", client=client)

    tool = ToolDefinition(name="read_file", description="Read a file.", parameters={"type": "object"})
    response = provider.chat(
        ChatRequest(messages=[Message(role="user", content="read a.txt")], tools=[tool])
    )

    assert response.has_tool_calls is True
    assert response.message.tool_calls is not None
    call = response.message.tool_calls[0]
    assert call.function.name == "read_file"
    assert call.function.arguments == {"path": "a.txt"}


def test_ollama_provider_raises_tools_not_supported_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "registry.ollama.ai/library/llama2 does not support tools"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://ollama.test", model="llama2", client=client)

    tool = ToolDefinition(name="read_file", description="Read a file.", parameters={"type": "object"})
    with pytest.raises(ToolsNotSupportedError, match="does not support tool calls"):
        provider.chat(
            ChatRequest(messages=[Message(role="user", content="hi")], tools=[tool])
        )


def test_create_provider_allows_ollama_without_configured_model() -> None:
    settings = ProviderSettings(name="ollama", model=None)

    provider = create_provider(settings)

    assert isinstance(provider, OllamaProvider)


def test_create_provider_rejects_unsupported_provider() -> None:
    settings = ProviderSettings(name="vllm", model="qwen")

    with pytest.raises(ProviderError, match="Unsupported provider"):
        create_provider(settings)
