from pydantic import Field

from app.schemas.api.api_model import ApiModel


# Corpo de POST /requisicoes: o pedido em texto livre digitado no chat.
class CreateRequisitionRequest(ApiModel):
    # Limita o tamanho do pedido (3 a 1000 caracteres) antes de chegar ao agente.
    request_text: str = Field(
        min_length=3,
        max_length=1000,
        description="Pedido em linguagem natural.",
        examples=["Preciso de 2 notebooks até US$ 1.500 cada para o time de vendas"],
    )
