from datetime import UTC, datetime, timedelta

from app.application.list_requisitions_use_case import ListRequisitionsUseCase
from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork
from tests.fakes.sample_snapshots import SampleSnapshots

# Instante base fixo para criar requisições com datas determinísticas.
START = datetime(2026, 11, 10, tzinfo=UTC)


# Cria requisições já persistidas para popular a listagem.
class RequisitionSeeder:
    # Id e data derivam dos minutos após START, para conferir a ordenação.
    @staticmethod
    def created(minutes_after_start: int) -> Requisition:
        return Requisition(
            id=minutes_after_start,
            request_text=f"pedido {minutes_after_start}",
            status=RequisitionStatus.COMPLETE,
            items=(RequisitionItem.from_snapshot(SampleSnapshots.LENOVO, 1),),
            agent_message="ok",
            created_at=START + timedelta(minutes=minutes_after_start),
        )


# A listagem traz as mais recentes primeiro e respeita o limite configurado.
def test_lists_newest_first_up_to_the_limit() -> None:
    committed = [RequisitionSeeder.created(minute) for minute in (1, 3, 2)]
    use_case = ListRequisitionsUseCase(InMemoryUnitOfWork(committed), limit=2)

    listed = use_case.execute()

    assert [requisition.id for requisition in listed] == [3, 2]
