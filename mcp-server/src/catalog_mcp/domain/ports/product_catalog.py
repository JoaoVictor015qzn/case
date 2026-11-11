from abc import ABC, abstractmethod

from catalog_mcp.schemas.product.product import Product
from catalog_mcp.schemas.product.product_category import ProductCategory


# Port do catálogo de produtos; a implementação real consulta a DummyJSON.
class ProductCatalog(ABC):
    @abstractmethod
    async def search(self, term: str) -> list[Product]:
        """Busca produtos por termo. Lista vazia quando nada corresponde."""

    @abstractmethod
    async def list_category(self, category: ProductCategory) -> list[Product]:
        """Todos os produtos de uma categoria."""

    @abstractmethod
    async def get(self, product_id: int) -> Product:
        """Busca um produto pelo id. Levanta ProductNotFoundError se não existir."""
