from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pricing.currency import Currency


class Money(BaseModel):
    """Valor monetário com duas casas decimais. Nunca usa float."""

    model_config = ConfigDict(frozen=True)

    CENTS: ClassVar[Decimal] = Decimal("0.01")

    amount: Decimal = Field(ge=0)
    currency: Currency = Currency.USD

    # Arredonda o valor para centavos (meio para cima) ao criar o objeto.
    @field_validator("amount")
    @classmethod
    def round_to_cents(cls, amount: Decimal) -> Decimal:
        return amount.quantize(cls.CENTS, rounding=ROUND_HALF_UP)

    # Cria um valor zerado, ponto de partida para somas.
    @classmethod
    def zero(cls, currency: Currency = Currency.USD) -> Self:
        return cls(amount=Decimal(0), currency=currency)

    # Soma dois valores; exige a mesma moeda.
    def add(self, other: Self) -> Self:
        self._ensure_same_currency(other)
        return type(self)(amount=self.amount + other.amount, currency=self.currency)

    # Multiplica o valor por uma quantidade inteira (preço unitário x quantidade).
    def multiply(self, quantity: int) -> Self:
        return type(self)(amount=self.amount * quantity, currency=self.currency)

    # Indica se este valor é maior que o outro; exige a mesma moeda.
    def exceeds(self, other: Self) -> bool:
        self._ensure_same_currency(other)
        return self.amount > other.amount

    # Formata para exibição, ex.: "USD 1,499.90".
    def display(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    # Lança erro se as duas moedas forem diferentes.
    def _ensure_same_currency(self, other: Self) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Moedas diferentes: {self.currency} e {other.currency}.")
