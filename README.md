# Orven

Orven is a Python command-line application for running local AI agents against local model providers. The product goal is a fast, terminal-native experience that feels close to Codex CLI, Claude Code, and Antigravity, while remaining focused on local execution and locally defined agent workflows.

## Project Mission

Orven exists to provide a serious local-agent CLI that can work with self-hosted and local-first model backends. Its mission is to make local agents usable in the same way modern coding CLIs are usable today: clear prompts, tool-driven workflows, reusable skills, and predictable execution.

The primary product goals are:

- integrate first with local model providers, especially `ollama` and `vLLM`
- feel and behave like a modern agent CLI rather than a basic chatbot wrapper
- support local skills that agents can discover, load, and follow consistently
- support structured workflows so agents can execute repeatable tasks correctly
- keep the developer experience simple: local config, typed code, and terminal-first ergonomics

## Product Direction

Orven is intended to act as an agent runtime and operator shell for local models. In practical terms, that means:

- model providers such as `ollama` and `vLLM` are first-class backends
- the CLI should support multi-step agent workflows instead of single prompt-response usage
- skills should be readable from the local filesystem and injected into agent behavior
- workflows should be explicitly defined so agents can execute them reliably
- the interface should feel responsive, structured, and coding-oriented

## Project Configuration

The repository is currently configured as a Python CLI scaffold for that larger goal:

- Package name: `orven`
- Version: `0.1.0`
- Python requirement: `>=3.12`
- Build backend: `hatchling`
- CLI entrypoint: `orven = "orven.main:app"`
- Source package path: `src/orven`

### Runtime Dependencies

- `httpx`
- `platformdirs`
- `prompt-toolkit`
- `pydantic`
- `pydantic-settings`
- `rich`
- `typer`

### Development Dependencies

- `mypy`
- `pytest`
- `ruff`

## Repository Layout

```text
.
|-- pyproject.toml
|-- uv.lock
|-- README.md
`-- src/
    `-- orven/
        |-- __init__.py
        `-- main.py
```

## Local Development

Install dependencies with `uv`:

```bash
uv sync
```

Run the CLI locally:

```bash
uv run orven hello
```

Run the main quality checks:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

## Current Status

The implementation is still at the scaffold stage. Right now the codebase provides:

- a `typer`-based CLI entrypoint
- dependency and packaging configuration through `pyproject.toml`
- development tooling for linting, type-checking, and tests
- a sample `hello` command for validating the CLI wiring

The next implementation phase is to add provider integration, local config loading, skill discovery, workflow definitions, and an interactive agent loop.
