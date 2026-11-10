from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.schemas.tools.product_detail import ProductDetail


class GetProductDetailUseCase:
    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog

    async def execute(self, product_id: int) -> ProductDetail:
        product = await self._catalog.get(product_id)
        return ProductDetail.from_product(product)
