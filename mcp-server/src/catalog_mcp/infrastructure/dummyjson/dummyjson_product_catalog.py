import httpx
from pydantic import BaseModel, ValidationError

from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from catalog_mcp.domain.errors.product_not_found_error import ProductNotFoundError
from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.infrastructure.dummyjson.dummyjson_http_client import DummyJsonHttpClient
from catalog_mcp.infrastructure.dummyjson.dummyjson_product_mapper import DummyJsonProductMapper
from catalog_mcp.schemas.dummyjson.dummyjson_product import DummyJsonProduct
from catalog_mcp.schemas.dummyjson.dummyjson_search_response import DummyJsonSearchResponse
from catalog_mcp.schemas.product.product import Product


class DummyJsonProductCatalog(ProductCatalog):
    """Implementa ProductCatalog sobre https://dummyjson.com/docs/products."""

    SEARCH_FIELDS = "id,title,category,price,stock,availabilityStatus,minimumOrderQuantity,brand"

    def __init__(
        self,
        http_client: DummyJsonHttpClient,
        mapper: DummyJsonProductMapper,
        search_limit: int,
    ) -> None:
        self._http_client = http_client
        self._mapper = mapper
        self._search_limit = search_limit

    async def search(self, term: str) -> list[Product]:
        params = {"q": term, "select": self.SEARCH_FIELDS, "limit": self._search_limit}
        response = await self._http_client.get("/products/search", params=params)
        payload = self._parse(response, DummyJsonSearchResponse)
        return [self._mapper.to_product(product) for product in payload.products]

    async def get(self, product_id: int) -> Product:
        response = await self._http_client.get(f"/products/{product_id}")
        if response.status_code == httpx.codes.NOT_FOUND:
            raise ProductNotFoundError(product_id)
        return self._mapper.to_product(self._parse(response, DummyJsonProduct))

    @staticmethod
    def _parse[T: BaseModel](response: httpx.Response, model: type[T]) -> T:
        if response.is_error:
            raise CatalogUnavailableError(f"a DummyJSON respondeu com erro {response.status_code}")
        try:
            return model.model_validate_json(response.content)
        except ValidationError as exc:
            raise CatalogUnavailableError("a DummyJSON devolveu uma resposta inesperada") from exc
