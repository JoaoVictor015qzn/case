from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.product.product import Product


# Saída estruturada da tool detalhar_produto, com marca e descrição.
class ProductDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    title: str
    category: str
    price: Money = Field(description="Preço unitário.")
    stock: int = Field(description="Unidades disponíveis em estoque.")
    minimum_order_quantity: int = Field(description="Quantidade mínima por pedido.")
    availability_status: str | None = None
    brand: str | None = None
    description: str | None = None

    # Converte a entidade Product no formato de detalhe da tool.
    @classmethod
    def from_product(cls, product: Product) -> Self:
        return cls.model_validate(product.model_dump())
