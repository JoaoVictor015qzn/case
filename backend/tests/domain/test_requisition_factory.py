import pytest

from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.sample_snapshots import SampleSnapshots

validator = GroundingValidator()
factory = RequisitionFactory()


def test_creates_complete_requisition_with_agent_message() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 1).build()

    requisition = factory.create("1 macbook", run, validator.validate(run), "chave-1")

    assert requisition.status is RequisitionStatus.COMPLETE
    assert requisition.agent_message == run.draft.message
    assert requisition.missing == ()
    assert requisition.idempotency_key == "chave-1"


def test_is_partial_when_agent_reports_missing() -> None:
    run = (
        AgentRunBuilder()
        .observed(SampleSnapshots.MACBOOK)
        .item(78, 1)
        .status(DraftStatus.PARTIAL)
        .missing("Mouse sem fio: não encontrado no catálogo.")
        .build()
    )

    requisition = factory.create("1 macbook e 1 mouse", run, validator.validate(run))

    assert requisition.status is RequisitionStatus.PARTIAL
    assert requisition.missing == ("Mouse sem fio: não encontrado no catálogo.",)


def test_rejections_make_it_partial_and_replace_the_message() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 1).item(999, 1).build()

    requisition = factory.create("pedido", run, validator.validate(run))

    assert requisition.status is RequisitionStatus.PARTIAL
    assert requisition.agent_message == RequisitionFactory.ADJUSTED_NOTICE
    assert len(requisition.missing) == 1


def test_raises_when_nothing_is_fulfillable() -> None:
    run = AgentRunBuilder().status(DraftStatus.UNFULFILLABLE).build()

    with pytest.raises(RequisitionNotFulfillableError) as error:
        factory.create("uma ferrari", run, validator.validate(run))

    assert error.value.missing == (RequisitionFactory.NOTHING_FOUND,)
