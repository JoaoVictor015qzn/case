from pydantic import Field, HttpUrl, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore", frozen=True)

    database_url: PostgresDsn
    openrouter_api_key: SecretStr
    openrouter_model: str = Field(min_length=1)
    openrouter_base_url: HttpUrl = HttpUrl("https://openrouter.ai/api/v1")
    llm_timeout_s: float = Field(default=60.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    mcp_url: HttpUrl = HttpUrl("http://mcp-server:8000/mcp")
    mcp_timeout_s: float = Field(default=30.0, gt=0)
    agent_max_iterations: int = Field(default=8, ge=1, le=20)
    requisitions_list_limit: int = Field(default=50, ge=1, le=500)
    log_level: str = "INFO"

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value
