"""create requisition tables

Revision ID: b270c52c7042
Revises:
Create Date: 2026-11-11 00:58:37.867642
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b270c52c7042"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tipo enum do Postgres usado na coluna requisition.status.
requisition_status = sa.Enum("COMPLETE", "PARTIAL", name="requisitionstatus")


# Cria as tabelas requisition e requisition_item com índices e restrições.
def upgrade() -> None:
    # Cabeçalho da requisição; idempotency_key única garante gravação única por chave.
    op.create_table(
        "requisition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_text", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("status", requisition_status, nullable=False),
        sa.Column("agent_message", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "missing",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("currency", sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("created_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_requisition_created_at"), "requisition", ["created_at"], unique=False)
    # Itens da requisição, apagados em cascata junto com ela.
    op.create_table(
        "requisition_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requisition_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_requisition_item_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_requisition_item_unit_price_non_negative"),
        sa.ForeignKeyConstraint(["requisition_id"], ["requisition.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_requisition_item_requisition_id"),
        "requisition_item",
        ["requisition_id"],
        unique=False,
    )


# Remove índices, tabelas e o tipo enum, na ordem inversa da criação.
def downgrade() -> None:
    op.drop_index(op.f("ix_requisition_item_requisition_id"), table_name="requisition_item")
    op.drop_table("requisition_item")
    op.drop_index(op.f("ix_requisition_created_at"), table_name="requisition")
    op.drop_table("requisition")
    requisition_status.drop(op.get_bind(), checkfirst=True)
