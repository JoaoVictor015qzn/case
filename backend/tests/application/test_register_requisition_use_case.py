from decimal import Decimal

import pytest

from app.application.register_requisition_use_case import RegisterRequisitionUseCase
from app.domain.errors.requisition_rejected_error import RequisitionRejectedError
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.requisition.requisition_status import RequisitionStatus
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork
from tests.fakes.registration_builder import RegistrationBuilder
from tests.fakes.sample_snapshots import SampleSnapshots

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# Caso de uso do endpoint interno com validador e fábrica reais e UoW em memória.
class RegisterHarness:
    def __init__(self) -> None:
        self.unit_of_work = InMemoryUnitOfWork()
        self.use_case = RegisterRequisitionUseCase(
            self.unit_of_work, GroundingValidator(), RequisitionFactory()
        )


# Grava a requisição com preço do catálogo, total calculado no backend e status completo.
async def test_saves_with_catalog_prices_and_computed_total() -> None:
    harness = RegisterHarness()

    created = await harness.use_case.execute(
        RegistrationBuilder().line(SampleSnapshots.MACBOOK, 2).build()
    )

    assert created.requisition.id == 1
    assert created.requisition.total.amount == Decimal("3999.98")
    assert created.requisition.status is RequisitionStatus.COMPLETE
    assert harness.unit_of_work.committed == [created.requisition]


# Itens faltantes informados deixam a requisição parcial.
async def test_missing_items_make_it_partial() -> None:
    registration = (
        RegistrationBuilder()
        .line(SampleSnapshots.LENOVO, 1)
        .missing("mouse: não encontrado")
        .build()
    )

    created = await RegisterHarness().use_case.execute(registration)

    assert created.requisition.status is RequisitionStatus.PARTIAL
    assert created.requisition.missing == ("mouse: não encontrado",)


# Violar estoque, pedido mínimo ou orçamento recusa tudo, mesmo com item válido junto.
@pytest.mark.parametrize(
    ("builder", "reason"),
    [
        (RegistrationBuilder().line(SampleSnapshots.MACBOOK, 25), "estoque"),
        (RegistrationBuilder().line(SampleSnapshots.IPHONE_6, 2), "mínima"),
        (
            RegistrationBuilder().line(SampleSnapshots.MACBOOK, 1).max_unit_price("1500"),
            "orçamento",
        ),
    ],
)
async def test_any_violation_rejects_everything_and_saves_nothing(
    builder: RegistrationBuilder, reason: str
) -> None:
    harness = RegisterHarness()

    with pytest.raises(RequisitionRejectedError) as error:
        await harness.use_case.execute(builder.line(SampleSnapshots.LENOVO, 1).build())

    assert reason in error.value.detail.lower()
    assert harness.unit_of_work.committed == []


# Registrar de novo com a mesma chave devolve a requisição existente, sem duplicar.
async def test_same_key_returns_the_existing_requisition() -> None:
    harness = RegisterHarness()
    registration = RegistrationBuilder().line(SampleSnapshots.LENOVO, 1).build()

    first = await harness.use_case.execute(registration)
    second = await harness.use_case.execute(registration)

    assert second.replayed is True
    assert second.requisition.id == first.requisition.id
    assert len(harness.unit_of_work.committed) == 1
