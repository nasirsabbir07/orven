# Add CLI smoke tests for the scaffold

## Summary

The repository declares `pytest` as a development dependency, but the test suite currently contains no tests.

## Evidence

- `pyproject.toml:21-24` includes `pytest`
- `README.md:81-86` documents `uv run pytest`
- Local verification: `pytest` collects `0 items`

## Problem

There is no automated protection for the only implemented behavior: CLI startup and output. That makes basic regressions easy to introduce while the command surface evolves.

## Proposed Outcome

Add a minimal smoke-test layer around the Typer CLI using `typer.testing.CliRunner` or an equivalent subprocess-level test.

## Acceptance Criteria

- At least one test verifies the main CLI invocation succeeds
- At least one test verifies `--help` output is available
- If `hello` remains, a test verifies its output
- `pytest` reports a non-zero number of collected tests
