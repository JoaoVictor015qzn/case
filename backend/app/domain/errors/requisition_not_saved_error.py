from app.domain.errors.domain_error import DomainError
from app.schemas.agent.tool_call_trace import ToolCallTrace


class RequisitionNotSavedError(DomainError):
    """O agente disse que montou a requisição, mas não a gravou por criar_requisicao."""

    user_message = "O agente montou a requisição, mas não conseguiu gravá-la. Tente novamente."

    # Guarda as chamadas de ferramenta para mostrar o que o agente tentou
    def __init__(self, detail: str, tool_calls: tuple[ToolCallTrace, ...] = ()) -> None:
        super().__init__(detail)
        self.tool_calls = tool_calls
