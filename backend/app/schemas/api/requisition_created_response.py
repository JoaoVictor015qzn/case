from typing import Self

from app.schemas.api.api_model import ApiModel
from app.schemas.api.requisition_public import RequisitionPublic
from app.schemas.api.tool_call_public import ToolCallPublic
from app.schemas.requisition.created_requisition import CreatedRequisition


class RequisitionCreatedResponse(ApiModel):
    requisition: RequisitionPublic
    message: str
    missing: list[str]
    tool_calls: list[ToolCallPublic]
    replayed: bool

    @classmethod
    def from_domain(cls, created: CreatedRequisition) -> Self:
        requisition = created.requisition
        return cls(
            requisition=RequisitionPublic.from_domain(requisition),
            message=requisition.agent_message,
            missing=list(requisition.missing),
            tool_calls=[ToolCallPublic.from_domain(trace) for trace in created.tool_calls],
            replayed=created.replayed,
        )
