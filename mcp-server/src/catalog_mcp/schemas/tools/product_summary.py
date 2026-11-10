from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.product.product import Product


class ProductSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Id do produto, usado em detalhar_produto.")
    title: str
    category: str
    price: Money = Field(description="Preço unitário.")
    stock: int = Field(description="Unidades disponíveis em estoque.")
    availability_status: str | None = None

    @classmethod
    def from_product(cls, product: Product) -> Self:
        return cls.model_validate(product.model_dump())
