from decimal import Decimal

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.infrastructure.persistence.tables.requisition_table import RequisitionTable


class RequisitionItemTable(SQLModel, table=True):
    """Snapshot do produto no momento da compra: o catálogo pode mudar depois."""

    __tablename__ = "requisition_item"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_requisition_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_requisition_item_unit_price_non_negative"),
    )

    id: int | None = Field(default=None, primary_key=True)
    requisition_id: int | None = Field(
        default=None,
        foreign_key="requisition.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    product_id: int
    title: str = Field(max_length=255)
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    quantity: int
    line_total: Decimal = Field(max_digits=12, decimal_places=2)

    requisition: RequisitionTable | None = Relationship(back_populates="items")
