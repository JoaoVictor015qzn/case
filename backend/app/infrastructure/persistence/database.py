from typing import Self

from sqlalchemy import Engine
from sqlmodel import Session, create_engine


class Database:
    """Dono do engine (pool de conexões). Criado uma vez no composition root."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_url(cls, url: str) -> Self:
        return cls(create_engine(url, pool_pre_ping=True))

    def session(self) -> Session:
        return Session(self._engine)

    def dispose(self) -> None:
        self._engine.dispose()
