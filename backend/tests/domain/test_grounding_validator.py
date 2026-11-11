from decimal import Decimal

from app.domain.services.grounding_validator import GroundingValidator
from app.schemas.grounding.grounding_candidate import GroundingCandidate
from app.schemas.pricing.budget import Budget
from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot
from tests.fakes.sample_snapshots import SampleSnapshots

validator = GroundingValidator()


# Monta candidatos de grounding: produto, quantidade e teto de preço opcional.
class Candidates:
    # Converte o teto em texto para Budget; sem teto, o candidato fica sem orçamento.
    @staticmethod
    def of(
        snapshot: ProductSnapshot, quantity: int, max_unit_price: str | None = None
    ) -> GroundingCandidate:
        budget = (
            None
            if max_unit_price is None
            else Budget(max_unit_price=Money(amount=Decimal(max_unit_price)))
        )
        return GroundingCandidate(snapshot=snapshot, quantity=quantity, budget=budget)


# Item válido é aceito com preço, título e total vindos do catálogo, não do LLM.
def test_accepts_product_with_price_from_snapshot() -> None:
    result = validator.validate([Candidates.of(SampleSnapshots.MACBOOK, 2)])

    assert result.is_clean
    (item,) = result.accepted
    assert item.unit_price.amount == Decimal("1999.99")
    assert item.title == SampleSnapshots.MACBOOK.title
    assert item.line_total.amount == Decimal("3999.98")


# Quantidade maior que o estoque é recusada.
def test_rejects_quantity_above_stock() -> None:
    result = validator.validate([Candidates.of(SampleSnapshots.MACBOOK, 25)])

    assert result.accepted == ()
    assert len(result.rejections) == 1


# Quantidade abaixo do pedido mínimo do produto é recusada.
def test_rejects_quantity_below_minimum_order() -> None:
    result = validator.validate([Candidates.of(SampleSnapshots.IPHONE_6, 2)])

    assert result.accepted == ()
    assert len(result.rejections) == 1


# Quantidade zero é recusada.
def test_rejects_non_positive_quantity() -> None:
    result = validator.validate([Candidates.of(SampleSnapshots.LENOVO, 0)])

    assert result.accepted == ()
    assert result.rejections


# Item acima do orçamento é recusado sem derrubar os demais itens válidos.
def test_rejects_price_above_budget_and_keeps_the_rest() -> None:
    result = validator.validate(
        [
            Candidates.of(SampleSnapshots.MACBOOK, 1, max_unit_price="1500"),
            Candidates.of(SampleSnapshots.LENOVO, 1, max_unit_price="1500"),
        ]
    )

    assert [item.product_id for item in result.accepted] == [81]
    assert len(result.rejections) == 1
