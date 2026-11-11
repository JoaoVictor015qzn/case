from pydantic import BaseModel, ConfigDict

from app.schemas.pricing.money import Money


class Budget(BaseModel):
    """Orçamento por unidade extraído do pedido (ex.: "até US$ 2.000 cada")."""

    model_config = ConfigDict(frozen=True)

    max_unit_price: Money

    # Aceita o preço unitário se ele não passar do teto do orçamento.
    def allows(self, unit_price: Money) -> bool:
        return not unit_price.exceeds(self.max_unit_price)
