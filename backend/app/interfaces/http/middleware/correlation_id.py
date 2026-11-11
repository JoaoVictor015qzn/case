import logging
from contextvars import ContextVar
from typing import ClassVar


class CorrelationId(logging.Filter):
    """Guarda o id do request atual e o injeta em todo registro de log (`%(correlation_id)s`)."""

    HEADER: ClassVar[str] = "X-Request-ID"
    NONE: ClassVar[str] = "-"
    _current: ClassVar[ContextVar[str]] = ContextVar("correlation_id", default=NONE)

    @classmethod
    def get(cls) -> str:
        return cls._current.get()

    @classmethod
    def set(cls, value: str) -> None:
        cls._current.set(value)

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.get()
        return True
