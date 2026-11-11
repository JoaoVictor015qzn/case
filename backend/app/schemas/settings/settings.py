from pydantic import Field, HttpUrl, SecretStr

from app.schemas.settings.database_settings import DatabaseSettings


# Configuração completa do backend lida do ambiente; falha no start se faltar algo.
class Settings(DatabaseSettings):
    openrouter_api_key: SecretStr
    # Token do endpoint interno chamado pelo MCP; exige ao menos 16 caracteres.
    internal_api_token: SecretStr = Field(min_length=16)
    openrouter_model: str = Field(min_length=1)
    openrouter_base_url: HttpUrl = HttpUrl("https://openrouter.ai/api/v1")
    llm_timeout_s: float = Field(default=60.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    mcp_url: HttpUrl = HttpUrl("http://mcp-server:8000/mcp")
    mcp_timeout_s: float = Field(default=30.0, gt=0)
    # Teto de rodadas do loop de tool calling do agente (1 a 20).
    agent_max_iterations: int = Field(default=8, ge=1, le=20)
    requisitions_list_limit: int = Field(default=50, ge=1, le=500)
    log_level: str = "INFO"
