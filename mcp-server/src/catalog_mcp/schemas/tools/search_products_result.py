from typing import Self

from pydantic import BaseModel, ConfigDict

from catalog_mcp.schemas.product.product import Product
from catalog_mcp.schemas.tools.product_summary import ProductSummary


# Saída estruturada da tool buscar_produtos: resumos encontrados e a contagem.
class SearchProductsResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    products: list[ProductSummary]
    total: int

    # Resume cada produto e calcula o total a partir da própria lista.
    @classmethod
    def from_products(cls, products: list[Product]) -> Self:
        summaries = [ProductSummary.from_product(product) for product in products]
        return cls(products=summaries, total=len(summaries))
