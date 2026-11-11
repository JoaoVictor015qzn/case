from pydantic import BaseModel, ConfigDict

from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.requisition.requisition import Requisition


class CreatedRequisition(BaseModel):
    """Resultado do caso de uso de criação: a requisição salva e o que o agente fez para chegar nela.

    `replayed` indica que a mesma Idempotency-Key já tinha criado a requisição; nesse caso o
    agente não roda de novo e não há `tool_calls`.
    """

    model_config = ConfigDict(frozen=True)

    requisition: Requisition
    tool_calls: tuple[ToolCallTrace, ...] = ()
    replayed: bool = False
