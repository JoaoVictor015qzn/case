from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.schemas.product.product import Product
from catalog_mcp.schemas.product.product_category import ProductCategory
from catalog_mcp.schemas.tools.search_products_result import SearchProductsResult


class SearchProductsUseCase:
    """Sem categoria, busca no catálogo todo. Com categoria, filtra a categoria pelo termo.

    Se nenhum produto da categoria tiver o termo no título ou na marca, devolve a categoria
    inteira: o modelo vê o que existe em vez de concluir que nada existe.
    """

    # Recebe o port do catálogo (DummyJSON em produção, fake nos testes).
    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog

    # Executa a busca por termo, opcionalmente restrita a uma categoria.
    async def execute(
        self, term: str, category: ProductCategory | None = None
    ) -> SearchProductsResult:
        # Sem categoria: delega a busca textual ao catálogo inteiro.
        if category is None:
            return SearchProductsResult.from_products(await self._catalog.search(term))
        # Com categoria: filtra pelo termo e, se nada casar, devolve a categoria toda.
        in_category = await self._catalog.list_category(category)
        matching = [product for product in in_category if self._matches(product, term)]
        return SearchProductsResult.from_products(matching or in_category)

    # Diz se alguma palavra do termo aparece no título ou na marca do produto.
    @staticmethod
    def _matches(product: Product, term: str) -> bool:
        haystack = f"{product.title} {product.brand or ''}".lower()
        return any(word in haystack for word in term.lower().split())
