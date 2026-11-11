from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.infrastructure.persistence.tables.requisition_item_table import RequisitionItemTable
from app.infrastructure.persistence.tables.requisition_table import RequisitionTable
from app.schemas.settings.database_settings import DatabaseSettings


class MigrationRunner:
    """Aplica as migrations com a URL do ambiente (12-factor), nunca a do alembic.ini."""

    TABLES = (RequisitionTable, RequisitionItemTable)

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._config = context.config
        if self._config.config_file_name is not None:
            fileConfig(self._config.config_file_name)

    def run(self) -> None:
        if context.is_offline_mode():
            self._run_offline()
        else:
            self._run_online()

    def _run_offline(self) -> None:
        context.configure(
            url=self._database_url,
            target_metadata=SQLModel.metadata,
            literal_binds=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    def _run_online(self) -> None:
        engine = engine_from_config(
            {"sqlalchemy.url": self._database_url}, prefix="sqlalchemy.", poolclass=pool.NullPool
        )
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=SQLModel.metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()


MigrationRunner(str(DatabaseSettings().database_url)).run()
