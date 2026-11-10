from pydantic import BaseModel, ConfigDict, Field

from catalog_mcp.schemas.pricing.money import Money


class Product(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int = Field(ge=1)
    title: str
    category: str
    price: Money
    stock: int = Field(ge=0)
    minimum_order_quantity: int = Field(default=1, ge=1)
    availability_status: str | None = None
    brand: str | None = None
    description: str | None = None
