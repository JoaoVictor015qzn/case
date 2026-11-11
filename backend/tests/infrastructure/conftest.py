from collections.abc import Iterator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.mappers.requisition_table_mapper import (
    RequisitionTableMapper,
)
from app.infrastructure.persistence.sqlmodel_unit_of_work import SqlModelUnitOfWork


# SQLite em memória com conexão única (StaticPool) e as tabelas criadas.
@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield Database(engine)
    engine.dispose()


# Unit of Work real do SQLModel sobre o banco de teste.
@pytest.fixture
def unit_of_work(database: Database) -> SqlModelUnitOfWork:
    return SqlModelUnitOfWork(database, RequisitionTableMapper())
