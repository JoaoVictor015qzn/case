from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EvalCase(BaseModel):
    """Um pedido em linguagem natural e o que o sistema deve devolver para ele."""

    model_config = ConfigDict(frozen=True)

    name: str
    request_text: str
    expect_status: int
    # Critérios opcionais conferidos só quando a requisição é criada (201).
    category: str | None = None
    quantity: int | None = None
    max_unit_price: Decimal | None = None
