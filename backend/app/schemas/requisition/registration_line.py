from pydantic import BaseModel, ConfigDict

from app.schemas.product.product_snapshot import ProductSnapshot


class RegistrationLine(BaseModel):
    """Produto relido do catálogo pelo MCP e a quantidade escolhida pelo agente."""

    model_config = ConfigDict(frozen=True)

    snapshot: ProductSnapshot
    quantity: int
