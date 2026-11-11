from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.schemas.requisition.requisition_status import RequisitionStatus

if TYPE_CHECKING:
    from app.infrastructure.persistence.tables.requisition_item_table import RequisitionItemTable


class RequisitionTable(SQLModel, table=True):
    __tablename__ = "requisition"

    id: int | None = Field(default=None, primary_key=True)
    request_text: str = Field(max_length=1000)
    status: RequisitionStatus
    agent_message: str
    missing: list[str] = Field(
        default_factory=list, sa_type=JSON().with_variant(JSONB(), "postgresql")
    )
    currency: str = Field(max_length=3)
    total_amount: Decimal = Field(max_digits=12, decimal_places=2)
    idempotency_key: str | None = Field(default=None, max_length=100, unique=True)
    created_at: datetime = Field(index=True)

    # Aspas obrigatórias: o SQLModel resolve a anotação ao criar a classe, e o import é circular.
    items: list["RequisitionItemTable"] = Relationship(  # noqa: UP037
        back_populates="requisition",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "RequisitionItemTable.id"},
    )
