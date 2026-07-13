# Fix CLI invocation docs and current command shape mismatch

## Summary

The README documents `uv run orven hello`, but the current Typer app exposes `hello` as the default command rather than a subcommand. Running the documented command fails.

## Evidence

- `README.md:78` documents `uv run orven hello`
- `src/orven/main.py:3-8` defines a single-command Typer app
- Local verification:
  - `.venv\Scripts\orven.exe hello` returns `Got unexpected extra argument(s) (hello)`
  - `.venv\Scripts\orven.exe --help` shows `Usage: orven [OPTIONS]`

## Problem

The first documented CLI invocation path is broken. That creates immediate friction for anyone trying to validate the scaffold and makes the CLI contract unclear before more commands are added.

## Proposed Outcome

Choose one contract and make the code and docs match:

- either keep `hello` as the default command and change the README to `uv run orven`
- or restructure the CLI so `hello` is an explicit subcommand and keep the current README example

## Acceptance Criteria

- The documented local run command succeeds on a clean environment
- `--help` output matches the intended command structure
- README examples are updated to the final behavior
- A regression test covers the invocation path
