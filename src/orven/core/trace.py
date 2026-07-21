from typing import Any, Literal

from pydantic import BaseModel, Field

StopReason = Literal["final_answer", "continue", "stagnant_loop", "max_iterations"]


class ToolCallRequest(BaseModel):
    tool_call_id: str
    name: str
    arguments: dict[str, Any]


class ToolInvocationRecord(BaseModel):
    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    result: str
    ok: bool


class TurnRecord(BaseModel):
    iteration: int
    prior_message_count: int
    assistant_content: str
    requested_tool_calls: list[ToolCallRequest] = Field(default_factory=list)
    tool_invocations: list[ToolInvocationRecord] = Field(default_factory=list)
    stop_reason: StopReason


__all__ = ["StopReason", "ToolCallRequest", "ToolInvocationRecord", "TurnRecord"]
