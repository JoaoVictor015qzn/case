from app.domain.errors.domain_error import DomainError
from app.domain.ports.purchasing_agent import PurchasingAgent
from app.domain.ports.unit_of_work import UnitOfWork
from app.schemas.agent.agent_request import AgentRequest
from app.schemas.agent.agent_run import AgentRun
from app.schemas.requisition.requisition import Requisition


class FakePurchasingAgent(PurchasingAgent):
    """Devolve um AgentRun pronto (ou levanta um erro) sem LLM e sem rede.

    Com `saves`, simula o agente chamando criar_requisicao: grava com a chave do pedido.
    """

    def __init__(
        self,
        run: AgentRun | None = None,
        error: DomainError | None = None,
        saves: Requisition | None = None,
        unit_of_work: UnitOfWork | None = None,
    ) -> None:
        self._run = run
        self._error = error
        self._saves = saves
        self._unit_of_work = unit_of_work
        self.calls = 0
        self.requests: list[AgentRequest] = []

    # Conta e guarda a chamada; levanta o erro, grava se configurado e devolve o AgentRun.
    async def run(self, request: AgentRequest) -> AgentRun:
        self.calls += 1
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        if self._run is None:
            raise AssertionError("FakePurchasingAgent sem AgentRun configurado")
        if self._saves is not None and self._unit_of_work is not None:
            self._save(self._saves, self._unit_of_work, request.idempotency_key)
        return self._run

    # Grava a requisição com a chave de idempotência do pedido, como faria a tool.
    @staticmethod
    def _save(requisition: Requisition, unit_of_work: UnitOfWork, idempotency_key: str) -> None:
        requisition = requisition.model_copy(update={"idempotency_key": idempotency_key})
        with unit_of_work:
            unit_of_work.requisitions.add(requisition)
            unit_of_work.commit()
