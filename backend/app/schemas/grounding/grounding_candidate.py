from pydantic import BaseModel, ConfigDict

from app.schemas.pricing.budget import Budget
from app.schemas.product.product_snapshot import ProductSnapshot


class GroundingCandidate(BaseModel):
    """Um produto observado, a quantidade proposta pelo agente e o orçamento do pedido."""

    model_config = ConfigDict(frozen=True)

    snapshot: ProductSnapshot
    quantity: int
    budget: Budget | None = None
