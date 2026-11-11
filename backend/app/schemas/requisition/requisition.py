from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.schemas.pricing.money import Money
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_status import RequisitionStatus


class Requisition(BaseModel):
    """Aggregate root do contexto Compras: só existe com itens válidos e calcula o próprio total."""

    model_config = ConfigDict(frozen=True)

    id: int | None = None
    request_text: str = Field(min_length=1, max_length=1000)
    status: RequisitionStatus
    # Invariante do agregado: sempre ao menos um item.
    items: tuple[RequisitionItem, ...] = Field(min_length=1)
    agent_message: str
    missing: tuple[str, ...] = ()
    idempotency_key: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Total calculado somando os subtotais dos itens, na moeda do primeiro item.
    @computed_field
    @property
    def total(self) -> Money:
        total = Money.zero(self.items[0].unit_price.currency)
        for item in self.items:
            total = total.add(item.line_total)
        return total

    # Recusa a requisição se o mesmo produto aparecer em mais de um item.
    @model_validator(mode="after")
    def ensure_unique_products(self) -> Self:
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Uma requisição não pode repetir o mesmo produto em itens diferentes.")
        return self

    # Devolve uma cópia com o id e a data atribuídos pelo banco ao salvar.
    def with_identity(self, requisition_id: int, created_at: datetime) -> Self:
        return self.model_copy(update={"id": requisition_id, "created_at": created_at})
