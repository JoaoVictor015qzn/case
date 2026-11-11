from app.domain.ports.unit_of_work import UnitOfWork
from app.schemas.requisition.requisition import Requisition


class ListRequisitionsUseCase:
    def __init__(self, unit_of_work: UnitOfWork, limit: int) -> None:
        self._unit_of_work = unit_of_work
        self._limit = limit

    def execute(self) -> list[Requisition]:
        with self._unit_of_work as unit_of_work:
            return unit_of_work.requisitions.list_recent(self._limit)
