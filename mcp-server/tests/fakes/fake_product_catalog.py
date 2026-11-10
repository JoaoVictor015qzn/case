from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from catalog_mcp.domain.errors.product_not_found_error import ProductNotFoundError
from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.schemas.product.product import Product


class FakeProductCatalog(ProductCatalog):
    def __init__(self, products: list[Product], *, unavailable: bool = False) -> None:
        self._products = {product.id: product for product in products}
        self._unavailable = unavailable

    async def search(self, term: str) -> list[Product]:
        self._fail_if_unavailable()
        needle = term.lower()
        return [
            product
            for product in self._products.values()
            if needle in product.title.lower() or needle in product.category
        ]

    async def get(self, product_id: int) -> Product:
        self._fail_if_unavailable()
        if product_id not in self._products:
            raise ProductNotFoundError(product_id)
        return self._products[product_id]

    def _fail_if_unavailable(self) -> None:
        if self._unavailable:
            raise CatalogUnavailableError("a DummyJSON não respondeu a tempo")
