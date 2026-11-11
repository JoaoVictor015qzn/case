from pydantic import Field

from app.schemas.api.api_model import ApiModel
from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot
from app.schemas.requisition.registration_line import RegistrationLine


class RegisterRequisitionItem(ApiModel):
    """Produto como o MCP acabou de ler do catálogo, mais a quantidade escolhida pelo agente."""

    product_id: int = Field(ge=1)
    title: str
    category: str
    unit_price: Money
    stock: int = Field(ge=0)
    minimum_order_quantity: int = Field(ge=1)
    quantity: int

    # Separa os dados do produto (snapshot) da quantidade e monta a linha de gravação.
    def to_line(self) -> RegistrationLine:
        snapshot = ProductSnapshot(
            product_id=self.product_id,
            title=self.title,
            category=self.category,
            unit_price=self.unit_price,
            stock=self.stock,
            minimum_order_quantity=self.minimum_order_quantity,
        )
        return RegistrationLine(snapshot=snapshot, quantity=self.quantity)
