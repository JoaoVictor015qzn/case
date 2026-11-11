from pydantic import BaseModel, ConfigDict, Field


class DraftItem(BaseModel):
    """Item proposto pelo LLM. Só vira item da requisição depois do grounding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    product_id: int = Field(
        description="Id do produto, exatamente como retornado por uma ferramenta."
    )
    quantity: int = Field(description="Quantidade pedida deste produto.")
    reason: str = Field(description="Por que este produto atende o pedido.")
