from app.infrastructure.persistence.tables.requisition_item_table import RequisitionItemTable
from app.infrastructure.persistence.tables.requisition_table import RequisitionTable
from app.schemas.pricing.currency import Currency
from app.schemas.pricing.money import Money
from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_item import RequisitionItem


class RequisitionTableMapper:
    """Agregado Requisition <-> linhas das tabelas. A tabela nunca sai da persistência."""

    def to_table(self, requisition: Requisition) -> RequisitionTable:
        return RequisitionTable(
            request_text=requisition.request_text,
            status=requisition.status,
            agent_message=requisition.agent_message,
            missing=list(requisition.missing),
            currency=requisition.total.currency.value,
            total_amount=requisition.total.amount,
            idempotency_key=requisition.idempotency_key,
            created_at=requisition.created_at,
            items=[self._item_to_table(item) for item in requisition.items],
        )

    def to_domain(self, row: RequisitionTable) -> Requisition:
        if row.id is None:
            raise ValueError("A requisição precisa ser gravada antes de virar agregado.")
        currency = Currency(row.currency)
        return Requisition(
            id=row.id,
            request_text=row.request_text,
            status=row.status,
            items=tuple(self._item_to_domain(item, currency) for item in row.items),
            agent_message=row.agent_message,
            missing=tuple(row.missing),
            idempotency_key=row.idempotency_key,
            created_at=row.created_at,
        )

    @staticmethod
    def _item_to_table(item: RequisitionItem) -> RequisitionItemTable:
        return RequisitionItemTable(
            product_id=item.product_id,
            title=item.title,
            unit_price=item.unit_price.amount,
            quantity=item.quantity,
            line_total=item.line_total.amount,
        )

    @staticmethod
    def _item_to_domain(row: RequisitionItemTable, currency: Currency) -> RequisitionItem:
        return RequisitionItem(
            product_id=row.product_id,
            title=row.title,
            unit_price=Money(amount=row.unit_price, currency=currency),
            quantity=row.quantity,
        )
