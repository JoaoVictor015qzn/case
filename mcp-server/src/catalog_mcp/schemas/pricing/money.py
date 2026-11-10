from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from catalog_mcp.schemas.pricing.currency import Currency


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal = Field(ge=0, description="Valor monetário.")
    currency: Currency = Field(default=Currency.USD, description="Moeda do valor.")
