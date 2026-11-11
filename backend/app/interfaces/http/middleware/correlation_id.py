import logging
from contextvars import ContextVar
from typing import ClassVar


class CorrelationId(logging.Filter):
    """Guarda o id do request atual e o injeta em todo registro de log (`%(correlation_id)s`)."""

    HEADER: ClassVar[str] = "X-Request-ID"
    # Valor exibido nos logs emitidos fora de um request.
    NONE: ClassVar[str] = "-"
    # ContextVar isola o id por request mesmo com várias tarefas async em paralelo.
    _current: ClassVar[ContextVar[str]] = ContextVar("correlation_id", default=NONE)

    # Lê o id do request atual.
    @classmethod
    def get(cls) -> str:
        return cls._current.get()

    # Define o id do request atual no contexto.
    @classmethod
    def set(cls, value: str) -> None:
        cls._current.set(value)

    # Acrescenta o correlation_id ao registro de log e sempre o deixa passar.
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.get()
        return True
