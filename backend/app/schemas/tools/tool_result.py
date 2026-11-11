import json

from pydantic import BaseModel, ConfigDict, JsonValue


class ToolResult(BaseModel):
    """Resultado de uma ferramenta: `structured_content` para o código, `text` para o modelo."""

    model_config = ConfigDict(frozen=True)

    is_error: bool
    text: str
    structured_content: dict[str, JsonValue] | None = None

    def model_output(self) -> str:
        if self.is_error or self.structured_content is None:
            return self.text
        return json.dumps(self.structured_content, ensure_ascii=False)
