from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore", frozen=True)

    dummyjson_base_url: HttpUrl = HttpUrl("https://dummyjson.com")
    dummyjson_timeout_s: float = Field(default=5.0, gt=0)
    dummyjson_max_attempts: int = Field(default=3, ge=1, le=5)
    dummyjson_retry_backoff_s: float = Field(default=0.3, ge=0)
    search_limit: int = Field(default=10, ge=1, le=100)
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    allowed_hosts: list[str] = [
        "mcp-server",
        "mcp-server:*",
        "localhost",
        "localhost:*",
        "127.0.0.1",
        "127.0.0.1:*",
    ]
    log_level: str = "INFO"
