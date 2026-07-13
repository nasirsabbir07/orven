# Introduce an explicit root CLI and subcommand structure

## Summary

The current CLI is a single function wired directly into `typer.Typer()`. That is enough for the scaffold, but it does not reflect the multi-command agent runtime described in the README.

## Evidence

- `src/orven/main.py:3-8` contains only a single `hello` command
- `README.md:21-25` describes provider backends, workflows, and a structured coding-oriented interface
- `README.md:98` says the next phase includes provider integration, config loading, skills, workflows, and an interactive agent loop

## Problem

Without an explicit root command and named subcommands, future expansion will be awkward. The current shape already caused a docs mismatch because the CLI effectively behaves as a single default command.

## Proposed Outcome

Refactor the CLI into a root app with a clear command tree, for example:

- `orven run`
- `orven providers`
- `orven skills`
- `orven workflows`
- `orven doctor`

The exact names can change, but the structure should support growth without breaking the mental model again.

## Acceptance Criteria

- `src/orven/main.py` no longer consists of a single default command only
- The root help screen presents named commands
- The command layout aligns with the next planned implementation phases
- Existing sample behavior is preserved through a subcommand or an equivalent smoke path
