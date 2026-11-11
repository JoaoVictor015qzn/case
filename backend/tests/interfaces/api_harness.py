from fastapi.testclient import TestClient

from app.application.create_requisition_use_case import CreateRequisitionUseCase
from app.application.list_requisitions_use_case import ListRequisitionsUseCase
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.interfaces.http.dependencies.use_case_provider import UseCaseProvider
from app.main import Application
from app.schemas.requisition.requisition import Requisition
from app.schemas.settings.settings import Settings
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork


class ApiHarness:
    """App real com os casos de uso trocados por versões sem LLM, sem MCP e sem banco."""

    def __init__(
        self, agent: FakePurchasingAgent | None = None, saved: list[Requisition] | None = None
    ) -> None:
        self.agent = agent or FakePurchasingAgent()
        self.unit_of_work = InMemoryUnitOfWork(saved)
        app = Application(Settings()).create()
        app.dependency_overrides[UseCaseProvider.create_requisition] = self._create_use_case
        app.dependency_overrides[UseCaseProvider.list_requisitions] = self._list_use_case
        self.client = TestClient(app, raise_server_exceptions=False)

    def _create_use_case(self) -> CreateRequisitionUseCase:
        return CreateRequisitionUseCase(
            self.agent, self.unit_of_work, GroundingValidator(), RequisitionFactory()
        )

    def _list_use_case(self) -> ListRequisitionsUseCase:
        return ListRequisitionsUseCase(self.unit_of_work, limit=50)
