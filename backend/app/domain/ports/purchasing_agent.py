from abc import ABC, abstractmethod

from app.schemas.agent.agent_run import AgentRun


class PurchasingAgent(ABC):
    @abstractmethod
    async def run(self, request_text: str) -> AgentRun:
        """Interpreta o pedido, consulta o catálogo pelas ferramentas e devolve o rascunho."""
