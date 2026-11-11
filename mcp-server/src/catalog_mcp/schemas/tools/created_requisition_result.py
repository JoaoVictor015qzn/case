from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.requisition.registration_response import RegistrationResponse


# Saída estruturada da tool criar_requisicao devolvida ao modelo.
class CreatedRequisitionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    requisition_id: int = Field(description="Número da requisição gravada.")
    status: str = Field(description="complete ou partial.")
    total: Money = Field(description="Total calculado pelo sistema com os preços do catálogo.")
    replayed: bool = Field(description="true se a requisição já tinha sido gravada antes.")

    # Achata a resposta do backend no formato enxuto exposto pela tool.
    @classmethod
    def from_registration(cls, registration: RegistrationResponse) -> Self:
        requisition = registration.requisition
        return cls(
            requisition_id=requisition.id,
            status=requisition.status,
            total=requisition.total,
            replayed=registration.replayed,
        )
