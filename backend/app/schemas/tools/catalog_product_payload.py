from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot


class CatalogProductPayload(BaseModel):
    """Produto no formato que as tools do servidor MCP devolvem (busca e detalhe)."""

    # Ignora campos extras que a tool devolva além dos usados aqui.
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int = Field(ge=1)
    title: str
    category: str
    price: Money
    stock: int = Field(ge=0)
    minimum_order_quantity: int = Field(ge=1)

    # Converte o payload da tool no snapshot de produto usado pelo domínio.
    def to_snapshot(self) -> ProductSnapshot:
        return ProductSnapshot(
            product_id=self.id,
            title=self.title,
            category=self.category,
            unit_price=self.price,
            stock=self.stock,
            minimum_order_quantity=self.minimum_order_quantity,
        )
