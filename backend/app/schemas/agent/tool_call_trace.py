from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ToolCallTrace(BaseModel):
    """Registro de uma chamada de ferramenta feita pelo agente (exibido no chat)."""

    model_config = ConfigDict(frozen=True)

    name: str
    arguments: dict[str, JsonValue]
    is_error: bool
    # Tempo da chamada em milissegundos; nunca negativo.
    duration_ms: int = Field(ge=0)
