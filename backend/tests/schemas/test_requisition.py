from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.sample_snapshots import SampleSnapshots


def test_total_sums_line_totals() -> None:
    requisition = Requisition(
        request_text="2 macbooks e 1 lenovo",
        status=RequisitionStatus.COMPLETE,
        items=(
            RequisitionItem.from_snapshot(SampleSnapshots.MACBOOK, 2),
            RequisitionItem.from_snapshot(SampleSnapshots.LENOVO, 1),
        ),
        agent_message="ok",
    )

    assert requisition.total.amount == Decimal("5099.97")
    assert requisition.model_dump(mode="json")["total"] == {"amount": "5099.97", "currency": "USD"}


def test_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        Requisition(
            request_text="nada",
            status=RequisitionStatus.COMPLETE,
            items=(),
            agent_message="ok",
        )


def test_rejects_repeated_product() -> None:
    item = RequisitionItem.from_snapshot(SampleSnapshots.MACBOOK, 1)

    with pytest.raises(ValidationError, match="repetir o mesmo produto"):
        Requisition(
            request_text="duplicado",
            status=RequisitionStatus.COMPLETE,
            items=(item, item),
            agent_message="ok",
        )


def test_with_identity_sets_id_and_creation_time() -> None:
    requisition = Requisition(
        request_text="1 macbook",
        status=RequisitionStatus.COMPLETE,
        items=(RequisitionItem.from_snapshot(SampleSnapshots.MACBOOK, 1),),
        agent_message="ok",
    )
    created_at = datetime(2026, 11, 11, tzinfo=UTC)

    persisted = requisition.with_identity(42, created_at)

    assert persisted.id == 42
    assert persisted.created_at == created_at
    assert requisition.id is None
