from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DummyJsonProduct(BaseModel):
    """Produto no formato da DummyJSON (camelCase). Não sai da camada de infraestrutura."""

    model_config = ConfigDict(frozen=True, alias_generator=to_camel, extra="ignore")

    id: int
    title: str
    category: str
    price: Decimal
    stock: int
    minimum_order_quantity: int = 1
    availability_status: str | None = None
    brand: str | None = None
    description: str | None = None
