from decimal import Decimal

from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot


# Snapshots de produtos do catálogo usados como dados de teste no backend.
class SampleSnapshots:
    MACBOOK = ProductSnapshot(
        product_id=78,
        title="Apple MacBook Pro 14 Inch Space Grey",
        category="laptops",
        unit_price=Money(amount=Decimal("1999.99")),
        stock=24,
    )
    LENOVO = ProductSnapshot(
        product_id=81,
        title="Lenovo Yoga 920",
        category="laptops",
        unit_price=Money(amount=Decimal("1099.99")),
        stock=40,
    )
    # Produto com pedido mínimo de 5 unidades, para testar essa regra.
    IPHONE_6 = ProductSnapshot(
        product_id=122,
        title="iPhone 6",
        category="smartphones",
        unit_price=Money(amount=Decimal("299.99")),
        stock=60,
        minimum_order_quantity=5,
    )
