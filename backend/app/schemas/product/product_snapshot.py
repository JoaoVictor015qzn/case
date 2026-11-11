from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pricing.money import Money


class ProductSnapshot(BaseModel):
    """Produto exatamente como uma tool do catálogo o devolveu nesta execução do agente."""

    model_config = ConfigDict(frozen=True)

    product_id: int = Field(ge=1)
    title: str
    category: str
    unit_price: Money
    stock: int = Field(ge=0)
    # Pedido mínimo do fornecedor; assume 1 quando a tool não informa.
    minimum_order_quantity: int = Field(default=1, ge=1)
