from decimal import Decimal

from pydantic import Field

from app.schemas.api.api_model import ApiModel
from app.schemas.api.register_requisition_item import RegisterRequisitionItem
from app.schemas.pricing.budget import Budget
from app.schemas.pricing.money import Money
from app.schemas.requisition.requisition_registration import RequisitionRegistration


class RegisterRequisitionRequest(ApiModel):
    """Corpo de POST /internal/requisicoes, enviado pelo servidor MCP (tool criar_requisicao)."""

    request_text: str = Field(min_length=1, max_length=1000)
    idempotency_key: str = Field(min_length=1, max_length=100)
    # Entre 1 e 20 itens por requisição.
    items: list[RegisterRequisitionItem] = Field(min_length=1, max_length=20)
    max_unit_price: Decimal | None = Field(default=None, ge=0)
    missing: list[str] = []
    message: str = Field(min_length=1, max_length=1000)

    # Converte o corpo HTTP no pedido de gravação usado pelo caso de uso.
    def to_registration(self) -> RequisitionRegistration:
        # Só monta o orçamento quando o pedido citou um teto por unidade.
        budget = (
            None
            if self.max_unit_price is None
            else Budget(max_unit_price=Money(amount=self.max_unit_price))
        )
        return RequisitionRegistration(
            request_text=self.request_text,
            idempotency_key=self.idempotency_key,
            lines=tuple(item.to_line() for item in self.items),
            budget=budget,
            missing=tuple(self.missing),
            message=self.message,
        )
