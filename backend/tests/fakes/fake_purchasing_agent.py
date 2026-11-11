from app.domain.errors.domain_error import DomainError
from app.domain.ports.purchasing_agent import PurchasingAgent
from app.schemas.agent.agent_run import AgentRun


class FakePurchasingAgent(PurchasingAgent):
    """Devolve um AgentRun pronto (ou levanta um erro) sem LLM e sem rede."""

    def __init__(self, run: AgentRun | None = None, error: DomainError | None = None) -> None:
        self._run = run
        self._error = error
        self.calls = 0

    async def run(self, request_text: str) -> AgentRun:
        self.calls += 1
        if self._error is not None:
            raise self._error
        if self._run is None:
            raise AssertionError("FakePurchasingAgent sem AgentRun configurado")
        return self._run
