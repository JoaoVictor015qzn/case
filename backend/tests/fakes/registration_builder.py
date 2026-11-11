from decimal import Decimal
from typing import Self

from app.schemas.pricing.budget import Budget
from app.schemas.pricing.money import Money
from app.schemas.product.product_snapshot import ProductSnapshot
from app.schemas.requisition.registration_line import RegistrationLine
from app.schemas.requisition.requisition_registration import RequisitionRegistration


class RegistrationBuilder:
    """Monta o que criar_requisicao envia ao backend, para testes."""

    def __init__(self, idempotency_key: str = "chave-1") -> None:
        self._idempotency_key = idempotency_key
        self._lines: list[RegistrationLine] = []
        self._budget: Budget | None = None
        self._missing: list[str] = []

    # Acrescenta um item com o snapshot do produto e a quantidade pedida.
    def line(self, snapshot: ProductSnapshot, quantity: int) -> Self:
        self._lines.append(RegistrationLine(snapshot=snapshot, quantity=quantity))
        return self

    # Define o orçamento como teto de preço unitário.
    def max_unit_price(self, value: str) -> Self:
        self._budget = Budget(max_unit_price=Money(amount=Decimal(value)))
        return self

    # Acrescenta itens do pedido que ficaram de fora (requisição parcial).
    def missing(self, *missing: str) -> Self:
        self._missing.extend(missing)
        return self

    # Gera o registro com texto e mensagem fixos e o que foi configurado.
    def build(self) -> RequisitionRegistration:
        return RequisitionRegistration(
            request_text="pedido de teste",
            idempotency_key=self._idempotency_key,
            lines=tuple(self._lines),
            budget=self._budget,
            missing=tuple(self._missing),
            message="Requisição montada.",
        )
