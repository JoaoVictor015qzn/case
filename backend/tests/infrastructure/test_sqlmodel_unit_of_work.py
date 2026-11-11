from decimal import Decimal

import pytest

from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.infrastructure.persistence.sqlmodel_unit_of_work import SqlModelUnitOfWork
from tests.fakes.requisition_samples import RequisitionSamples


def test_round_trips_the_aggregate_with_exact_money(unit_of_work: SqlModelUnitOfWork) -> None:
    requisition = RequisitionSamples.two_laptops(idempotency_key="chave-1")

    with unit_of_work:
        saved = unit_of_work.requisitions.add(requisition)
        unit_of_work.commit()
    with unit_of_work:
        found = unit_of_work.requisitions.find_by_idempotency_key("chave-1")

    assert saved.id is not None
    assert found == saved
    assert found.total.amount == Decimal("4199.97")
    assert [item.product_id for item in found.items] == [78, 81]
    assert found.missing == ("Mouse sem fio: não encontrado.",)
    assert found.created_at == requisition.created_at


def test_nothing_is_saved_without_commit(unit_of_work: SqlModelUnitOfWork) -> None:
    with unit_of_work:
        unit_of_work.requisitions.add(RequisitionSamples.two_laptops())

    with unit_of_work:
        assert unit_of_work.requisitions.list_recent(10) == []


def test_lists_newest_first_up_to_the_limit(unit_of_work: SqlModelUnitOfWork) -> None:
    with unit_of_work:
        for minute in (1, 3, 2):
            unit_of_work.requisitions.add(
                RequisitionSamples.two_laptops(minutes_after_start=minute)
            )
        unit_of_work.commit()

    with unit_of_work:
        listed = unit_of_work.requisitions.list_recent(2)

    assert [requisition.created_at.minute for requisition in listed] == [3, 2]


def test_duplicate_idempotency_key_is_a_domain_error(unit_of_work: SqlModelUnitOfWork) -> None:
    with unit_of_work:
        unit_of_work.requisitions.add(RequisitionSamples.two_laptops(idempotency_key="chave-1"))
        unit_of_work.commit()

    with unit_of_work, pytest.raises(DuplicateIdempotencyKeyError):
        unit_of_work.requisitions.add(RequisitionSamples.two_laptops(idempotency_key="chave-1"))


def test_unknown_idempotency_key_returns_none(unit_of_work: SqlModelUnitOfWork) -> None:
    with unit_of_work:
        assert unit_of_work.requisitions.find_by_idempotency_key("nao-existe") is None
