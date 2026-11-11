from typing import cast

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import Session, col, select

from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.domain.ports.requisition_repository import RequisitionRepository
from app.infrastructure.persistence.mappers.requisition_table_mapper import (
    RequisitionTableMapper,
)
from app.infrastructure.persistence.tables.requisition_item_table import RequisitionItemTable
from app.infrastructure.persistence.tables.requisition_table import RequisitionTable
from app.schemas.requisition.requisition import Requisition


class SqlModelRequisitionRepository(RequisitionRepository):
    IDEMPOTENCY_COLUMN = "idempotency_key"
    # Em runtime o atributo é instrumentado pelo SQLAlchemy; o SQLModel o tipa como a lista.
    LOAD_ITEMS = selectinload(
        cast(QueryableAttribute[list[RequisitionItemTable]], RequisitionTable.items)
    )

    def __init__(self, session: Session, mapper: RequisitionTableMapper) -> None:
        self._session = session
        self._mapper = mapper

    def add(self, requisition: Requisition) -> Requisition:
        row = self._mapper.to_table(requisition)
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as error:
            key = requisition.idempotency_key
            if key is not None and self.IDEMPOTENCY_COLUMN in str(error.orig):
                raise DuplicateIdempotencyKeyError(key) from error
            raise
        return self._mapper.to_domain(row)

    def find_by_idempotency_key(self, idempotency_key: str) -> Requisition | None:
        statement = (
            select(RequisitionTable)
            .where(col(RequisitionTable.idempotency_key) == idempotency_key)
            .options(self.LOAD_ITEMS)
        )
        row = self._session.exec(statement).first()
        return None if row is None else self._mapper.to_domain(row)

    def list_recent(self, limit: int) -> list[Requisition]:
        statement = (
            select(RequisitionTable)
            .options(self.LOAD_ITEMS)
            .order_by(col(RequisitionTable.created_at).desc(), col(RequisitionTable.id).desc())
            .limit(limit)
        )
        return [self._mapper.to_domain(row) for row in self._session.exec(statement).all()]
