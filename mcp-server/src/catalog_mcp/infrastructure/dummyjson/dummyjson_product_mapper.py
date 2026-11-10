from catalog_mcp.schemas.dummyjson.dummyjson_product import DummyJsonProduct
from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.product.product import Product


class DummyJsonProductMapper:
    """Camada anticorrupção: traduz o formato da DummyJSON para a entidade Product."""

    def to_product(self, source: DummyJsonProduct) -> Product:
        return Product(
            id=source.id,
            title=source.title,
            category=source.category,
            price=Money(amount=source.price),
            stock=source.stock,
            minimum_order_quantity=source.minimum_order_quantity,
            availability_status=source.availability_status,
            brand=source.brand,
            description=source.description,
        )
