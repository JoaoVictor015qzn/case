from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.infrastructure.persistence.tables.requisition_item_table import RequisitionItemTable
from app.infrastructure.persistence.tables.requisition_table import RequisitionTable
from app.schemas.settings.database_settings import DatabaseSettings


class MigrationRunner:
    """Aplica as migrations com a URL do ambiente (12-factor), nunca a do alembic.ini."""

    # Referencia as tabelas para registrá-las no SQLModel.metadata usado pelo Alembic.
    TABLES = (RequisitionTable, RequisitionItemTable)

    # Guarda a URL do banco e aplica a configuração de logging do alembic.ini.
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._config = context.config
        if self._config.config_file_name is not None:
            fileConfig(self._config.config_file_name)

    # Escolhe o modo offline (gera SQL) ou online (conecta e aplica).
    def run(self) -> None:
        if context.is_offline_mode():
            self._run_offline()
        else:
            self._run_online()

    # Emite o SQL das migrations sem abrir conexão com o banco.
    def _run_offline(self) -> None:
        context.configure(
            url=self._database_url,
            target_metadata=SQLModel.metadata,
            literal_binds=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    # Conecta ao banco sem pool e aplica as migrations numa transação.
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


# Ponto de entrada do Alembic: lê a URL do banco do ambiente e roda as migrations.
MigrationRunner(str(DatabaseSettings().database_url)).run()
