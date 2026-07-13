from __future__ import annotations

from typing import Any

import httpx

from orven.providers.base import (
    ModelInfo,
    ModelProvider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
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

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = self.model or self._default_model()
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": request.prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
        except httpx.ConnectError as error:
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            ) from error
        except httpx.HTTPStatusError as error:
            raise ProviderError(_format_ollama_status_error(error)) from error
        except httpx.HTTPError as error:
            raise ProviderError(f"Ollama request failed: {error}") from error

        data = response.json()
        text = data.get("response")
        if not isinstance(text, str):
            raise ProviderError("Ollama returned an invalid response payload.")

        model = data.get("model")
        return ProviderResponse(
            text=text,
            model=model if isinstance(model, str) else self.model or "",
            provider=self.name,
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
            raise ProviderError(_format_ollama_status_error(error)) from error
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


def _format_ollama_status_error(error: httpx.HTTPStatusError) -> str:
    status_code = error.response.status_code
    details = _read_error_detail(error.response)

    if status_code == 404:
        return f"Ollama model or endpoint was not found. {details}".strip()

    return f"Ollama returned HTTP {status_code}. {details}".strip()


def _read_error_detail(response: httpx.Response) -> str:
    try:
        data: Any = response.json()
    except ValueError:
        text = response.text.strip()
        return text if text else ""

    detail = data.get("error") if isinstance(data, dict) else None
    return str(detail) if detail else ""
