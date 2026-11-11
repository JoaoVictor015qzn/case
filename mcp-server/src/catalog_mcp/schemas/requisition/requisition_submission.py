from decimal import Decimal

from catalog_mcp.schemas.requisition.camel_model import CamelModel
from catalog_mcp.schemas.requisition.requisition_submission_item import RequisitionSubmissionItem


# Corpo enviado ao POST /internal/requisicoes do backend.
class RequisitionSubmission(CamelModel):
    request_text: str
    idempotency_key: str
    items: list[RequisitionSubmissionItem]
    max_unit_price: Decimal | None
    missing: list[str]
    message: str
