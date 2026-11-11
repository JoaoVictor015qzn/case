from pydantic import BaseModel, ConfigDict, Field


# Item informado pelo modelo em criar_requisicao: só id do produto e quantidade.
class RequisitionItemArgument(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: int = Field(ge=1, description="Id do produto, retornado por buscar_produtos.")
    quantity: int = Field(ge=1, description="Quantidade a comprar.")
