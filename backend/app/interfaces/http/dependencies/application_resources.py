from typing import Self

from openai import AsyncOpenAI

from app.infrastructure.persistence.database import Database
from app.schemas.settings.settings import Settings


class ApplicationResources:
    """Recursos de vida longa (pool de conexões e cliente HTTP do LLM), criados no lifespan."""

    # Guarda o cliente do LLM e o Database compartilhados entre requests.
    def __init__(self, llm_client: AsyncOpenAI, database: Database) -> None:
        self.llm_client = llm_client
        self.database = database

    # Cria o cliente OpenRouter (timeout e retries) e o engine do banco a partir das Settings.
    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        llm_client = AsyncOpenAI(
            base_url=str(settings.openrouter_base_url),
            api_key=settings.openrouter_api_key.get_secret_value(),
            timeout=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )
        return cls(llm_client, Database.from_url(str(settings.database_url)))

    # Fecha o cliente HTTP do LLM e o pool do banco no fim do lifespan.
    async def close(self) -> None:
        await self.llm_client.close()
        self.database.dispose()
