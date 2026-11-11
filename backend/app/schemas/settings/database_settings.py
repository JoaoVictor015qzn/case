from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Só o que as migrations precisam: rodar o Alembic não exige a chave da OpenRouter."""

    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore", frozen=True)

    database_url: PostgresDsn

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value
