from pydantic import BaseModel, ConfigDict, JsonValue


class ToolDefinition(BaseModel):
    """Ferramenta do catálogo como o agente a vê, independente do protocolo (MCP)."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    input_schema: dict[str, JsonValue]
