from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.schemas.tools.search_products_result import SearchProductsResult


class SearchProductsUseCase:
    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog

    async def execute(self, term: str) -> SearchProductsResult:
        products = await self._catalog.search(term)
        return SearchProductsResult.from_products(products)
