from types import TracebackType
from typing import Self

from sqlmodel import Session

from app.domain.ports.unit_of_work import UnitOfWork
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.mappers.requisition_table_mapper import (
    RequisitionTableMapper,
)
from app.infrastructure.persistence.sqlmodel_requisition_repository import (
    SqlModelRequisitionRepository,
)


class SqlModelUnitOfWork(UnitOfWork):
    """Uma Session por bloco `with`: requisição e itens gravados juntos no commit, ou nada."""

    # Guarda o Database e o mapper; a Session só é aberta ao entrar no `with`.
    def __init__(self, database: Database, mapper: RequisitionTableMapper) -> None:
        self._database = database
        self._mapper = mapper
        self._session: Session | None = None

    # Abre a Session e cria o repositório ligado a ela.
    def __enter__(self) -> Self:
        self._session = self._database.session()
        self.requisitions = SqlModelRequisitionRepository(self._session, self._mapper)
        return self

    # Desfaz o que não foi commitado e fecha a Session, com ou sem erro.
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = self._active_session()
        session.rollback()
        session.close()
        self._session = None

    # Confirma a transação: requisição e itens gravados de uma vez.
    def commit(self) -> None:
        self._active_session().commit()

    # Devolve a Session aberta ou falha se usada fora do `with`.
    def _active_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Use o Unit of Work dentro de um bloco `with`.")
        return self._session
