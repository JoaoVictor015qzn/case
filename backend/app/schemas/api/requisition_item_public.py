from typing import Self

from app.schemas.api.api_model import ApiModel
from app.schemas.pricing.money import Money
from app.schemas.requisition.requisition_item import RequisitionItem


# Item da requisição como a API expõe ao chat, com o subtotal da linha.
class RequisitionItemPublic(ApiModel):
    product_id: int
    title: str
    unit_price: Money
    quantity: int
    line_total: Money

    # Converte o item do domínio no DTO da API.
    @classmethod
    def from_domain(cls, item: RequisitionItem) -> Self:
        return cls(
            product_id=item.product_id,
            title=item.title,
            unit_price=item.unit_price,
            quantity=item.quantity,
            line_total=item.line_total,
        )
