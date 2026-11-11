from typing import Self

from pydantic import JsonValue

from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.api.api_model import ApiModel


class ToolCallPublic(ApiModel):
    name: str
    arguments: dict[str, JsonValue]
    is_error: bool
    duration_ms: int

    @classmethod
    def from_domain(cls, trace: ToolCallTrace) -> Self:
        return cls(
            name=trace.name,
            arguments=trace.arguments,
            is_error=trace.is_error,
            duration_ms=trace.duration_ms,
        )
