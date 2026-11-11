from decimal import Decimal

from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.product.product import Product


# Produtos de exemplo (ids reais da DummyJSON) usados pelo catálogo falso.
class SampleProducts:
    MACBOOK = Product(
        id=78,
        title="Apple MacBook Pro 14 Inch Space Grey",
        category="laptops",
        price=Money(amount=Decimal("1999.99")),
        stock=24,
        availability_status="In Stock",
        brand="Apple",
    )
    LENOVO = Product(
        id=81,
        title="Lenovo Yoga 920",
        category="laptops",
        price=Money(amount=Decimal("1099.99")),
        stock=40,
    )

    # Todos os produtos de exemplo, para popular o catálogo.
    @classmethod
    def all(cls) -> list[Product]:
        return [cls.MACBOOK, cls.LENOVO]
