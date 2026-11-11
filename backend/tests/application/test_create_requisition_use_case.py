from decimal import Decimal

import pytest

from app.application.create_requisition_use_case import CreateRequisitionUseCase
from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork
from tests.fakes.sample_snapshots import SampleSnapshots

pytestmark = pytest.mark.anyio


class UseCaseHarness:
    def __init__(self, run: AgentRun) -> None:
        self.agent = FakePurchasingAgent(run)
        self.unit_of_work = InMemoryUnitOfWork()
        self.use_case = CreateRequisitionUseCase(
            self.agent, self.unit_of_work, GroundingValidator(), RequisitionFactory()
        )


async def test_saves_requisition_with_prices_from_the_catalog() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 2).build()
    harness = UseCaseHarness(run)

    created = await harness.use_case.execute("2 macbooks")

    assert created.requisition.id == 1
    assert created.requisition.total.amount == Decimal("3999.98")
    assert created.replayed is False
    assert harness.unit_of_work.committed == [created.requisition]


async def test_returns_the_tool_calls_of_the_run() -> None:
    run = (
        AgentRunBuilder()
        .observed(SampleSnapshots.MACBOOK)
        .tool_call("buscar_produtos")
        .item(78, 1)
        .build()
    )
    harness = UseCaseHarness(run)

    created = await harness.use_case.execute("1 macbook")

    assert [call.name for call in created.tool_calls] == ["buscar_produtos"]


async def test_saves_nothing_when_nothing_is_fulfillable() -> None:
    harness = UseCaseHarness(AgentRunBuilder().status(DraftStatus.UNFULFILLABLE).build())

    with pytest.raises(RequisitionNotFulfillableError):
        await harness.use_case.execute("uma ferrari")

    assert harness.unit_of_work.committed == []


async def test_discards_unobserved_item_and_saves_the_rest_as_partial() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.LENOVO).item(81, 1).item(999, 1).build()
    harness = UseCaseHarness(run)

    created = await harness.use_case.execute("pedido")

    assert [item.product_id for item in created.requisition.items] == [81]
    assert created.requisition.status is RequisitionStatus.PARTIAL


async def test_same_idempotency_key_does_not_run_the_agent_twice() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 1).build()
    harness = UseCaseHarness(run)

    first = await harness.use_case.execute("1 macbook", "chave-1")
    second = await harness.use_case.execute("1 macbook", "chave-1")

    assert second.replayed is True
    assert second.requisition.id == first.requisition.id
    assert harness.agent.calls == 1
    assert len(harness.unit_of_work.committed) == 1


async def test_agent_errors_propagate_without_saving() -> None:
    agent = FakePurchasingAgent(error=LLMTimeoutError())
    unit_of_work = InMemoryUnitOfWork()
    use_case = CreateRequisitionUseCase(
        agent, unit_of_work, GroundingValidator(), RequisitionFactory()
    )

    with pytest.raises(LLMTimeoutError):
        await use_case.execute("1 macbook")

    assert unit_of_work.committed == []
