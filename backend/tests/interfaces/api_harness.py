from fastapi.testclient import TestClient

from app.application.create_requisition_use_case import CreateRequisitionUseCase
from app.application.list_requisitions_use_case import ListRequisitionsUseCase
from app.application.register_requisition_use_case import RegisterRequisitionUseCase
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.interfaces.http.dependencies.use_case_provider import UseCaseProvider
from app.main import Application
from app.schemas.agent.agent_run import AgentRun
from app.schemas.requisition.requisition import Requisition
from app.schemas.settings.settings import Settings
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork


class ApiHarness:
    """App real com os casos de uso trocados por versões sem LLM, sem MCP e sem banco."""

    # Cabeçalho com o mesmo token definido em INTERNAL_API_TOKEN no conftest.
    INTERNAL_HEADERS = {"X-Internal-Token": "token-interno-de-teste"}

    def __init__(
        self,
        run: AgentRun | None = None,
        *,
        agent_saves: Requisition | None = None,
        agent: FakePurchasingAgent | None = None,
        saved: list[Requisition] | None = None,
    ) -> None:
        self.unit_of_work = InMemoryUnitOfWork(saved)
        self.agent = agent or FakePurchasingAgent(
            run, saves=agent_saves, unit_of_work=self.unit_of_work
        )
        app = Application(Settings()).create()
        app.dependency_overrides[UseCaseProvider.create_requisition] = self._create_use_case
        app.dependency_overrides[UseCaseProvider.register_requisition] = self._register_use_case
        app.dependency_overrides[UseCaseProvider.list_requisitions] = self._list_use_case
        self.client = TestClient(app, raise_server_exceptions=False)

    # Caso de uso de POST /requisicoes com o agente falso.
    def _create_use_case(self) -> CreateRequisitionUseCase:
        return CreateRequisitionUseCase(self.agent, self.unit_of_work)

    # Caso de uso do endpoint interno com validação de grounding real.
    def _register_use_case(self) -> RegisterRequisitionUseCase:
        return RegisterRequisitionUseCase(
            self.unit_of_work, GroundingValidator(), RequisitionFactory()
        )

    # Caso de uso de GET /requisicoes sobre a mesma UoW em memória.
    def _list_use_case(self) -> ListRequisitionsUseCase:
        return ListRequisitionsUseCase(self.unit_of_work, limit=50)
