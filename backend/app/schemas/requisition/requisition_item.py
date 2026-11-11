from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot


class RequisitionItem(BaseModel):
    """Item da requisição. Título e preço são o snapshot do catálogo, nunca o texto do LLM."""

    model_config = ConfigDict(frozen=True)

    product_id: int = Field(ge=1)
    title: str
    unit_price: Money
    quantity: int = Field(ge=1)

    # Subtotal da linha (preço unitário x quantidade), incluído na serialização.
    @computed_field
    @property
    def line_total(self) -> Money:
        return self.unit_price.multiply(self.quantity)

    # Cria o item copiando título e preço do snapshot do catálogo.
    @classmethod
    def from_snapshot(cls, snapshot: ProductSnapshot, quantity: int) -> Self:
        return cls(
            product_id=snapshot.product_id,
            title=snapshot.title,
            unit_price=snapshot.unit_price,
            quantity=quantity,
        )
