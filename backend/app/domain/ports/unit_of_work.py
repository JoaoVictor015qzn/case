from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.domain.ports.requisition_repository import RequisitionRepository


class UnitOfWork(ABC):
    """Uma transação por caso de uso: ou tudo é gravado no commit, ou nada é."""

    # Repositório de requisições ligado à transação corrente
    requisitions: RequisitionRepository

    # Abre a transação
    @abstractmethod
    def __enter__(self) -> Self: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Desfaz o que não foi commitado e libera a conexão."""

    # Confirma tudo o que foi registrado na transação
    @abstractmethod
    def commit(self) -> None: ...
