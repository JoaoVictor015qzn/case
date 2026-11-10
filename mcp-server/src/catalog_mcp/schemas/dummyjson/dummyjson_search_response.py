from pydantic import BaseModel, ConfigDict

from catalog_mcp.schemas.dummyjson.dummyjson_product import DummyJsonProduct


class DummyJsonSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    products: list[DummyJsonProduct]
    total: int
