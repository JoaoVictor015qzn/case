from decimal import Decimal

from catalog_mcp.domain.errors.requisition_registry_unavailable_error import (
    RequisitionRegistryUnavailableError,
)
from catalog_mcp.domain.errors.requisition_rejected_error import RequisitionRejectedError
from catalog_mcp.domain.ports.requisition_registry import RequisitionRegistry
from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.requisition.registered_requisition import RegisteredRequisition
from catalog_mcp.schemas.requisition.registration_response import RegistrationResponse
from catalog_mcp.schemas.requisition.requisition_submission import RequisitionSubmission


class FakeRequisitionRegistry(RequisitionRegistry):
    """Guarda o que receberia o backend e responde como ele, sem rede."""

    def __init__(self, *, rejection: str | None = None, unavailable: bool = False) -> None:
        self._rejection = rejection
        self._unavailable = unavailable
        self.submissions: list[RequisitionSubmission] = []

    # Falha conforme configurado ou guarda o envio e devolve id sequencial e total calculado.
    async def register(self, submission: RequisitionSubmission) -> RegistrationResponse:
        if self._unavailable:
            raise RequisitionRegistryUnavailableError("não foi possível conectar ao backend")
        if self._rejection is not None:
            raise RequisitionRejectedError(self._rejection)
        self.submissions.append(submission)
        total = sum(
            (item.unit_price.amount * item.quantity for item in submission.items), Decimal("0")
        )
        requisition = RegisteredRequisition(
            id=len(self.submissions),
            status="partial" if submission.missing else "complete",
            total=Money(amount=total),
        )
        return RegistrationResponse(requisition=requisition)
