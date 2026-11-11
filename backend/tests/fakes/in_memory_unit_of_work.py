from types import TracebackType
from typing import Self

from app.domain.ports.unit_of_work import UnitOfWork
from app.schemas.requisition.requisition import Requisition
from tests.fakes.in_memory_requisition_repository import InMemoryRequisitionRepository


class InMemoryUnitOfWork(UnitOfWork):
    """Só o que passou por commit() fica em `committed`, como numa transação real."""

    def __init__(self, committed: list[Requisition] | None = None) -> None:
        self.committed: list[Requisition] = committed if committed is not None else []
        self.commits = 0
        self._repository = InMemoryRequisitionRepository(self.committed)

    def __enter__(self) -> Self:
        self._repository = InMemoryRequisitionRepository(self.committed)
        self.requisitions = self._repository
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._repository.pending.clear()

    def commit(self) -> None:
        self.committed.extend(self._repository.pending)
        self._repository.pending.clear()
        self.commits += 1
