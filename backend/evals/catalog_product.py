from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CatalogProduct(BaseModel):
    """Produto como a DummyJSON devolve: a referência independente para conferir a requisição."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int
    title: str
    category: str
    price: Decimal
