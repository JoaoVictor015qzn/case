import httpx

from evals.catalog_product import CatalogProduct


class CatalogReference:
    """Consulta a DummyJSON direto, sem passar pelo MCP, para não conferir o sistema com ele mesmo."""

    # Recebe um cliente HTTP apontado para a DummyJSON e inicia o cache por id.
    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._cache: dict[int, CatalogProduct | None] = {}

    # Busca o produto por id (uma vez só); devolve None se a DummyJSON não o encontrar.
    def get(self, product_id: int) -> CatalogProduct | None:
        if product_id not in self._cache:
            response = self._client.get(f"/products/{product_id}")
            self._cache[product_id] = (
                CatalogProduct.model_validate(response.json()) if response.is_success else None
            )
        return self._cache[product_id]
