from decimal import Decimal

from app.domain.services.grounding_validator import GroundingValidator
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.sample_snapshots import SampleSnapshots

validator = GroundingValidator()


def test_accepts_observed_product_with_price_from_snapshot() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 2).build()

    result = validator.validate(run)

    assert result.is_clean
    (item,) = result.accepted
    assert item.unit_price.amount == Decimal("1999.99")
    assert item.title == SampleSnapshots.MACBOOK.title
    assert item.line_total.amount == Decimal("3999.98")


def test_rejects_product_not_observed_in_this_run() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(999, 1).build()

    result = validator.validate(run)

    assert result.accepted == ()
    assert "Produto 999" in result.rejections[0]


def test_merges_duplicate_product_lines() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.LENOVO).item(81, 1).item(81, 2).build()

    (item,) = validator.validate(run).accepted

    assert item.quantity == 3


def test_rejects_quantity_above_stock() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.MACBOOK).item(78, 25).build()

    result = validator.validate(run)

    assert result.accepted == ()
    assert len(result.rejections) == 1


def test_rejects_quantity_below_minimum_order() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.IPHONE_6).item(122, 2).build()

    result = validator.validate(run)

    assert result.accepted == ()
    assert len(result.rejections) == 1


def test_rejects_non_positive_quantity() -> None:
    run = AgentRunBuilder().observed(SampleSnapshots.LENOVO).item(81, 0).build()

    result = validator.validate(run)

    assert result.accepted == ()
    assert result.rejections


def test_rejects_price_above_budget_and_keeps_the_rest() -> None:
    run = (
        AgentRunBuilder()
        .observed(SampleSnapshots.MACBOOK, SampleSnapshots.LENOVO)
        .max_unit_price(1500)
        .item(78, 1)
        .item(81, 1)
        .build()
    )

    result = validator.validate(run)

    assert [item.product_id for item in result.accepted] == [81]
    assert len(result.rejections) == 1
