# Implement provider abstraction and first Ollama backend

## Summary

The project mission is centered on local model providers, especially Ollama and vLLM, but the runtime currently has no provider abstraction or backend implementation.

## Evidence

- `README.md:11` identifies `ollama` and `vLLM` as primary targets
- `README.md:21` says model providers are first-class backends
- `pyproject.toml:8` includes `httpx`, but no provider code exists under `src/orven`

## Problem

The repository cannot yet exercise its main product value: talking to a local model provider. Until this exists, other agent features remain mostly theoretical.

## Proposed Outcome

Add a provider interface plus a first concrete Ollama backend that can execute a minimal chat or completion request against a local server.

## Acceptance Criteria

- A provider abstraction exists with clear request and response models
- An Ollama implementation can be configured with base URL and model name
- The CLI can execute a minimal end-to-end prompt against Ollama
- Errors such as connection failures and missing models are surfaced clearly
- Tests cover the provider adapter with mocked HTTP responses
