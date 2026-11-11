from app.schemas.api.api_model import ApiModel
from app.schemas.api.tool_call_public import ToolCallPublic


class ErrorResponse(ApiModel):
    """Corpo de todo erro da API. `detail` é texto em pt-BR que o chat exibe como está."""

    detail: str
    missing: list[str] = []
    tool_calls: list[ToolCallPublic] = []
