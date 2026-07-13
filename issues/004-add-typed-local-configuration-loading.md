# Add typed local configuration loading

## Summary

The package already depends on `pydantic-settings` and `platformdirs`, but there is no configuration model or local config loading yet.

## Evidence

- `pyproject.toml:9-12` includes `platformdirs`, `pydantic`, and `pydantic-settings`
- `src/orven/main.py:1-11` does not load configuration or define settings
- `README.md:98` lists local config loading as a next implementation phase

## Problem

Provider integration, skills, and workflows will all need predictable config resolution. Delaying this means later features will either duplicate config logic or hardcode paths that become migration problems.

## Proposed Outcome

Introduce a typed settings layer that supports:

- application-level config paths derived from `platformdirs`
- environment variable overrides
- a local config file format for provider defaults and runtime behavior
- validation errors with user-readable CLI output

## Acceptance Criteria

- A typed settings model exists in the package
- The CLI can resolve and display the active config path
- Missing or invalid config produces actionable errors
- At least one test covers config loading and validation
