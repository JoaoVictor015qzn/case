from abc import ABC, abstractmethod

from catalog_mcp.schemas.product.product import Product


class ProductCatalog(ABC):
    @abstractmethod
    async def search(self, term: str) -> list[Product]:
        """Busca produtos por termo. Lista vazia quando nada corresponde."""

    @abstractmethod
    async def get(self, product_id: int) -> Product:
        """Busca um produto pelo id. Levanta ProductNotFoundError se não existir."""
