# Add local skill and workflow discovery

## Summary

The README positions skills and structured workflows as core differentiators, but the package has no filesystem discovery or loading mechanism for either.

## Evidence

- `README.md:13-14` lists reusable skills and repeatable workflows as primary goals
- `README.md:23-24` says skills should be readable from the local filesystem and workflows should be explicitly defined
- `README.md:98` names skill discovery and workflow definitions as the next implementation phase
- `src/orven` currently contains only `main.py` and an empty `__init__.py`

## Problem

Without local discovery and loading, the product cannot deliver on its intended agent behavior model. This is one of the core pieces that separates an agent CLI from a plain prompt wrapper.

## Proposed Outcome

Define a local filesystem convention and loader for:

- skills
- workflow definitions
- validation and parse errors
- command(s) to inspect discovered assets

## Acceptance Criteria

- The package defines canonical directories or config-driven locations for skills and workflows
- A loader can enumerate and parse local definitions
- The CLI exposes a read-only inspection command such as `skills list` or `workflows list`
- Invalid files produce actionable diagnostics instead of silent failure
- Tests cover discovery behavior for valid and invalid fixtures
