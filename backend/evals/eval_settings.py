from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvalSettings(BaseSettings):
    """Onde está o sistema no ar e qual a nota mínima. Variáveis com prefixo EVALS_."""

    model_config = SettingsConfigDict(env_prefix="EVALS_", frozen=True)

    # Backend no ar e catálogo de referência.
    base_url: str = "http://localhost:8000"
    catalog_url: str = "https://dummyjson.com"
    # Acertos mínimos para o script sair com código 0.
    min_passed: int = Field(default=4, ge=0)
    # Tempo máximo por pedido, já que cada um roda o agente inteiro.
    timeout_s: float = Field(default=180, gt=0)
