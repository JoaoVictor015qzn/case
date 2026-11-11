from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pricing.budget import Budget
from app.schemas.requisition.registration_line import RegistrationLine


class RequisitionRegistration(BaseModel):
    """Pedido de gravação feito pelo agente via criar_requisicao."""

    model_config = ConfigDict(frozen=True)

    request_text: str
    idempotency_key: str
    # Exige ao menos uma linha: não se grava requisição vazia.
    lines: tuple[RegistrationLine, ...] = Field(min_length=1)
    budget: Budget | None = None
    missing: tuple[str, ...] = ()
    message: str
