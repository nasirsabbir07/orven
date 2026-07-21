import typer

from orven.core.trace import TurnRecord

_RESULT_PREVIEW_LIMIT = 200
_LOUD_STOP_REASONS = {"stagnant_loop", "max_iterations"}


def print_turn_receipt(record: TurnRecord) -> None:
    """Print a one-line-per-tool-call summary of a turn to stderr."""
    invocations_by_id = {
        invocation.tool_call_id: invocation for invocation in record.tool_invocations
    }

    for requested in record.requested_tool_calls:
        invocation = invocations_by_id.get(requested.tool_call_id)
        args_preview = ", ".join(f"{key}={value!r}" for key, value in requested.arguments.items())
        call_preview = f"{requested.name}({args_preview})"

        if invocation is None:
            typer.echo(f"[turn {record.iteration}] {call_preview} -> not executed", err=True)
            continue

        status = "ok" if invocation.ok else "error"
        result_preview = _truncate(invocation.result)
        typer.echo(f"[turn {record.iteration}] {call_preview} -> {status}: {result_preview}", err=True)

    if record.stop_reason in _LOUD_STOP_REASONS:
        typer.echo(f"[turn {record.iteration}] stopped: {record.stop_reason}", err=True)


def _truncate(text: str, *, limit: int = _RESULT_PREVIEW_LIMIT) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"
