from typing import Self

from sqlalchemy import Engine
from sqlmodel import Session, create_engine


class Database:
    """Dono do engine (pool de conexões). Criado uma vez no composition root."""

    # Recebe um engine já criado, dono do pool de conexões.
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # Cria o engine a partir da URL, testando a conexão antes de reutilizá-la do pool.
    @classmethod
    def from_url(cls, url: str) -> Self:
        return cls(create_engine(url, pool_pre_ping=True))

    # Abre uma nova Session sobre o engine compartilhado.
    def session(self) -> Session:
        return Session(self._engine)

    # Fecha as conexões do pool no desligamento da aplicação.
    def dispose(self) -> None:
        self._engine.dispose()
