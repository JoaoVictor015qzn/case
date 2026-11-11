from app.domain.errors.domain_error import DomainError
from app.schemas.agent.tool_call_trace import ToolCallTrace


# Erro quando nenhum produto do catálogo atende o pedido e nada é gravado (HTTP 422)
class RequisitionNotFulfillableError(DomainError):
    user_message = "Nenhum produto do catálogo atende o pedido. Nada foi salvo."

    # Guarda o que faltou, a mensagem do agente e as chamadas de ferramenta feitas
    def __init__(
        self,
        missing: tuple[str, ...],
        agent_message: str = "",
        tool_calls: tuple[ToolCallTrace, ...] = (),
    ) -> None:
        super().__init__("; ".join(missing))
        self.missing = missing
        self.agent_message = agent_message or self.user_message
        self.tool_calls = tool_calls
