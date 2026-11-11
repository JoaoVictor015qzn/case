from datetime import datetime
from typing import Self

from app.schemas.api.api_model import ApiModel
from app.schemas.api.requisition_item_public import RequisitionItemPublic
from app.schemas.pricing.money import Money
from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_status import RequisitionStatus


class RequisitionPublic(ApiModel):
    id: int
    request_text: str
    status: RequisitionStatus
    items: list[RequisitionItemPublic]
    total: Money
    message: str
    missing: list[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, requisition: Requisition) -> Self:
        if requisition.id is None:
            raise ValueError("Só requisições já salvas são expostas pela API.")
        return cls(
            id=requisition.id,
            request_text=requisition.request_text,
            status=requisition.status,
            items=[RequisitionItemPublic.from_domain(item) for item in requisition.items],
            total=requisition.total,
            message=requisition.agent_message,
            missing=list(requisition.missing),
            created_at=requisition.created_at,
        )
