from typing import Self

from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.product.product import Product
from catalog_mcp.schemas.requisition.camel_model import CamelModel


class RequisitionSubmissionItem(CamelModel):
    """Produto com os dados lidos agora do catálogo; nada aqui vem do modelo, exceto a quantidade."""

    product_id: int
    title: str
    category: str
    unit_price: Money
    stock: int
    minimum_order_quantity: int
    quantity: int

    # Monta o item a partir do produto do catálogo e da quantidade pedida.
    @classmethod
    def from_product(cls, product: Product, quantity: int) -> Self:
        return cls(
            product_id=product.id,
            title=product.title,
            category=product.category,
            unit_price=product.price,
            stock=product.stock,
            minimum_order_quantity=product.minimum_order_quantity,
            quantity=quantity,
        )
