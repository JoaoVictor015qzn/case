from pydantic import BaseModel, ConfigDict, Field


class AgentRequest(BaseModel):
    """O que o agente recebe. A chave de idempotência vai para criar_requisicao sem passar pelo LLM."""

    model_config = ConfigDict(frozen=True)

    request_text: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=100)
