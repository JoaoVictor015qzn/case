from abc import ABC, abstractmethod

from app.schemas.agent.agent_request import AgentRequest
from app.schemas.agent.agent_run import AgentRun


# Porta do agente de compras que interpreta o pedido usando o LLM
class PurchasingAgent(ABC):
    @abstractmethod
    async def run(self, request: AgentRequest) -> AgentRun:
        """Interpreta o pedido, consulta o catálogo e, se decidir, grava a requisição pela tool."""
