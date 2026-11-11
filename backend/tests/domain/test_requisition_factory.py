from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.registration_builder import RegistrationBuilder
from tests.fakes.sample_snapshots import SampleSnapshots

factory = RequisitionFactory()
MACBOOK_ITEM = RequisitionItem.from_snapshot(SampleSnapshots.MACBOOK, 1)


# Sem faltantes, a requisição sai completa, com a mensagem do agente e a chave do pedido.
def test_creates_complete_requisition_with_agent_message_and_key() -> None:
    registration = RegistrationBuilder("chave-1").line(SampleSnapshots.MACBOOK, 1).build()

    requisition = factory.create(registration, [MACBOOK_ITEM])

    assert requisition.status is RequisitionStatus.COMPLETE
    assert requisition.agent_message == registration.message
    assert requisition.missing == ()
    assert requisition.idempotency_key == "chave-1"


# Com itens faltantes informados pelo agente, a requisição fica parcial e os lista.
def test_is_partial_when_agent_reports_missing() -> None:
    registration = (
        RegistrationBuilder()
        .line(SampleSnapshots.MACBOOK, 1)
        .missing("Mouse sem fio: não encontrado no catálogo.")
        .build()
    )

    requisition = factory.create(registration, [MACBOOK_ITEM])

    assert requisition.status is RequisitionStatus.PARTIAL
    assert requisition.missing == ("Mouse sem fio: não encontrado no catálogo.",)
