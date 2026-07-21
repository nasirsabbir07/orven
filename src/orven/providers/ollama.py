from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from orven.providers.base import (
    ChatRequest,
    ChatResponse,
    Message,
    ModelInfo,
    ModelProvider,
    ProviderError,
    ToolCall,
    ToolCallFunction,
    ToolsNotSupportedError,
)


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(
        self,
        *,
        base_url: str,
        model: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = client or httpx.Client(timeout=60.0)
        self._owns_client = client is None

    def chat(
        self,
        request: ChatRequest,
        *,
        on_token: Callable[[str], None] | None = None,
    ) -> ChatResponse:
        model = self.model or self._default_model()
        payload: dict[str, Any] = {
            "model": model,
            "messages": [_to_ollama_message(message) for message in request.messages],
            "stream": on_token is not None,
        }
        if request.tools:
            payload["tools"] = [tool.to_openai_function() for tool in request.tools]

        tools_requested = bool(request.tools)

        if on_token is not None:
            return self._stream_chat(payload, model, on_token, tools_requested=tools_requested)

        try:
            response = self._client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
        except httpx.ConnectError as error:
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            ) from error
        except httpx.HTTPStatusError as error:
            raise _translate_status_error(error, tools_requested=tools_requested) from error
        except httpx.HTTPError as error:
            raise ProviderError(f"Ollama request failed: {error}") from error

        return _parse_chat_payload(response.json(), model, self.name)

    def _stream_chat(
        self,
        payload: dict[str, Any],
        model: str,
        on_token: Callable[[str], None],
        *,
        tools_requested: bool,
    ) -> ChatResponse:
        content_parts: list[str] = []
        final_tool_calls: list[dict[str, Any]] | None = None
        final_model = model

        try:
            with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    error.response.read()
                    raise _translate_status_error(
                        error, tools_requested=tools_requested
                    ) from error

                for line in response.iter_lines():
                    if not line:
                        continue

                    chunk = json.loads(line)
                    message = chunk.get("message") or {}
                    delta = message.get("content")
                    if delta:
                        content_parts.append(delta)
                        on_token(delta)

                    if message.get("tool_calls"):
                        final_tool_calls = message["tool_calls"]

                    if chunk.get("done"):
                        final_model = chunk.get("model") or model
                        break
        except httpx.ConnectError as error:
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            ) from error
        except httpx.HTTPError as error:
            raise ProviderError(f"Ollama request failed: {error}") from error

        return _parse_chat_payload(
            {
                "message": {"content": "".join(content_parts), "tool_calls": final_tool_calls},
                "model": final_model,
            },
            model,
            self.name,
        )

    def list_models(self) -> list[ModelInfo]:
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
        except httpx.ConnectError as error:
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            ) from error
        except httpx.HTTPStatusError as error:
            raise _translate_status_error(error, tools_requested=False) from error
        except httpx.HTTPError as error:
            raise ProviderError(f"Ollama request failed: {error}") from error

        data = response.json()
        models = data.get("models")
        if not isinstance(models, list):
            raise ProviderError("Ollama returned an invalid model list payload.")

        model_infos: list[ModelInfo] = []
        for model in models:
            if isinstance(model, dict) and isinstance(model.get("name"), str):
                model_infos.append(ModelInfo(name=model["name"]))

        return model_infos

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _default_model(self) -> str:
        models = self.list_models()
        if not models:
            raise ProviderError(
                "No Ollama models are installed. Run `ollama pull <model>` or set "
                "ORVEN_PROVIDER__MODEL to an installed model."
            )

        return models[0].name


def _to_ollama_message(message: Message) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                }
            }
            for tool_call in message.tool_calls
        ]
    return payload


def _parse_chat_payload(data: dict[str, Any], model: str, provider_name: str) -> ChatResponse:
    message = data.get("message")
    if not isinstance(message, dict):
        raise ProviderError("Ollama returned an invalid response payload.")

    content = message.get("content")
    content = content if isinstance(content, str) else ""

    raw_calls = message.get("tool_calls") or []
    tool_calls: list[ToolCall] = []
    for index, raw_call in enumerate(raw_calls):
        function = raw_call.get("function") if isinstance(raw_call, dict) else None
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            raise ProviderError("Ollama returned a malformed tool call.")

        arguments = _coerce_arguments(function.get("arguments"), function["name"])
        tool_calls.append(
            ToolCall(
                id=f"call_{index}",
                function=ToolCallFunction(name=function["name"], arguments=arguments),
            )
        )

    response_model = data.get("model")
    return ChatResponse(
        message=Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls or None,
        ),
        model=response_model if isinstance(response_model, str) else model,
        provider=provider_name,
    )


def _coerce_arguments(raw_arguments: Any, tool_name: str) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError as error:
            raise ProviderError(
                f"Model returned malformed tool call arguments for '{tool_name}'."
            ) from error
        if isinstance(parsed, dict):
            return parsed

    raise ProviderError(f"Model returned malformed tool call arguments for '{tool_name}'.")


def _translate_status_error(
    error: httpx.HTTPStatusError, *, tools_requested: bool
) -> ProviderError:
    status_code = error.response.status_code
    details = _read_error_detail(error.response)

    if tools_requested and status_code == 400 and _looks_like_missing_tool_support(details):
        return ToolsNotSupportedError(
            f"The configured model does not support tool calls. {details} "
            "Choose a tool-capable model (e.g. llama3.1, qwen2.5, mistral-nemo) via "
            "`orven model` or ORVEN_PROVIDER__MODEL."
        )

    if status_code == 404:
        return ProviderError(f"Ollama model or endpoint was not found. {details}".strip())

    return ProviderError(f"Ollama returned HTTP {status_code}. {details}".strip())


def _looks_like_missing_tool_support(details: str) -> bool:
    lowered = details.lower()
    return "does not support tool" in lowered


def _read_error_detail(response: httpx.Response) -> str:
    try:
        data: Any = response.json()
    except ValueError:
        text = response.text.strip()
        return text if text else ""

    detail = data.get("error") if isinstance(data, dict) else None
    return str(detail) if detail else ""
