from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.schemas.tools.product_detail import ProductDetail


# Caso de uso da tool detalhar_produto: lê um produto do catálogo pelo id.
class GetProductDetailUseCase:
    # Recebe o port do catálogo (DummyJSON em produção, fake nos testes).
    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog

    # Busca o produto e converte para o formato de detalhe devolvido pela tool.
    async def execute(self, product_id: int) -> ProductDetail:
        product = await self._catalog.get(product_id)
        return ProductDetail.from_product(product)
