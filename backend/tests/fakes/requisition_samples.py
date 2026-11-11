from datetime import UTC, datetime, timedelta

from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.sample_snapshots import SampleSnapshots


class RequisitionSamples:
    START = datetime(2026, 11, 10, 12, tzinfo=UTC)

    @classmethod
    def two_laptops(
        cls, idempotency_key: str | None = None, minutes_after_start: int = 0
    ) -> Requisition:
        return Requisition(
            request_text="1 macbook e 2 lenovos",
            status=RequisitionStatus.PARTIAL,
            items=(
                RequisitionItem.from_snapshot(SampleSnapshots.MACBOOK, 1),
                RequisitionItem.from_snapshot(SampleSnapshots.LENOVO, 2),
            ),
            agent_message="Montei a requisição.",
            missing=("Mouse sem fio: não encontrado.",),
            idempotency_key=idempotency_key,
            created_at=cls.START + timedelta(minutes=minutes_after_start),
        )
