from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.pricing.budget import Budget
from app.schemas.pricing.money import Money


# Valores são arredondados para centavos, com meio para cima.
def test_rounds_to_cents_half_up() -> None:
    assert Money(amount=Decimal("10.005")).amount == Decimal("10.01")


# Valor monetário negativo é inválido.
def test_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        Money(amount=Decimal("-1"))


# Multiplicar e somar usam Decimal exato, sem erro de ponto flutuante.
def test_multiply_and_add_keep_exact_decimal() -> None:
    total = Money(amount=Decimal("0.10")).multiply(3).add(Money(amount=Decimal("0.20")))

    assert total.amount == Decimal("0.50")


# No JSON, o valor sai como texto para não perder precisão, junto da moeda.
def test_serializes_amount_as_string() -> None:
    assert Money(amount=Decimal("1999.99")).model_dump(mode="json") == {
        "amount": "1999.99",
        "currency": "USD",
    }


# O orçamento aceita preço igual ao teto e recusa um centavo acima.
def test_budget_allows_price_equal_to_limit() -> None:
    budget = Budget(max_unit_price=Money(amount=Decimal("1500")))

    assert budget.allows(Money(amount=Decimal("1500.00"))) is True
    assert budget.allows(Money(amount=Decimal("1500.01"))) is False
