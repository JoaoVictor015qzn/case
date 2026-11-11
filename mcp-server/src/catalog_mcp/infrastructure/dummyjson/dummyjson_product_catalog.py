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
from catalog_mcp.schemas.product.product_category import ProductCategory


class DummyJsonProductCatalog(ProductCatalog):
    """Implementa ProductCatalog sobre https://dummyjson.com/docs/products."""

    # Campos pedidos à DummyJSON nas listagens (select), para respostas enxutas.
    SEARCH_FIELDS = "id,title,category,price,stock,availabilityStatus,minimumOrderQuantity,brand"

    # Recebe o cliente HTTP, o mapper anticorrupção e o limite de resultados por busca.
    def __init__(
        self,
        http_client: DummyJsonHttpClient,
        mapper: DummyJsonProductMapper,
        search_limit: int,
    ) -> None:
        self._http_client = http_client
        self._mapper = mapper
        self._search_limit = search_limit

    # Busca textual em /products/search, limitada a search_limit resultados.
    async def search(self, term: str) -> list[Product]:
        params = {"q": term, "select": self.SEARCH_FIELDS, "limit": self._search_limit}
        response = await self._http_client.get("/products/search", params=params)
        payload = self._parse(response, DummyJsonSearchResponse)
        return [self._mapper.to_product(product) for product in payload.products]

    # Lista todos os produtos da categoria (limit=0 desliga a paginação da DummyJSON).
    async def list_category(self, category: ProductCategory) -> list[Product]:
        params = {"select": self.SEARCH_FIELDS, "limit": 0}
        response = await self._http_client.get(f"/products/category/{category}", params=params)
        payload = self._parse(response, DummyJsonSearchResponse)
        return [self._mapper.to_product(product) for product in payload.products]

    # Lê um produto pelo id; 404 da DummyJSON vira ProductNotFoundError.
    async def get(self, product_id: int) -> Product:
        response = await self._http_client.get(f"/products/{product_id}")
        if response.status_code == httpx.codes.NOT_FOUND:
            raise ProductNotFoundError(product_id)
        return self._mapper.to_product(self._parse(response, DummyJsonProduct))

    # Valida a resposta no schema Pydantic; erro HTTP ou JSON inesperado vira indisponível.
    @staticmethod
    def _parse[T: BaseModel](response: httpx.Response, model: type[T]) -> T:
        if response.is_error:
            raise CatalogUnavailableError(f"a DummyJSON respondeu com erro {response.status_code}")
        # Payload fora do formato esperado não deve vazar para o modelo como dado válido.
        try:
            return model.model_validate_json(response.content)
        except ValidationError as exc:
            raise CatalogUnavailableError("a DummyJSON devolveu uma resposta inesperada") from exc
