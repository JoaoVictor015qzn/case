from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent.draft_item import DraftItem
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.pricing.budget import Budget
from app.schemas.pricing.money import Money


class RequisitionDraft(BaseModel):
    """Saída estruturada do LLM (json_schema strict): todos os campos obrigatórios, sem extras."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Sem description: em strict, um $ref (enum em $defs) não pode ter palavras-chave irmãs.
    status: DraftStatus
    # float só no formato de fio do LLM: Decimal geraria um schema com pattern que alguns
    # providers recusam em strict. A conversão para Money acontece em budget().
    max_unit_price: float | None = Field(
        description="Orçamento máximo por unidade em USD citado no pedido, ou null se não houver."
    )
    items: list[DraftItem] = Field(description="Itens escolhidos. Vazio se nada atender.")
    missing: list[str] = Field(description="O que não foi possível atender e por quê.")
    message: str = Field(description="Resposta curta ao usuário, em português.")

    # Converte o teto em float do LLM para Budget com Money (via str, sem erro de float).
    def budget(self) -> Budget | None:
        if self.max_unit_price is None:
            return None
        return Budget(max_unit_price=Money(amount=Decimal(str(self.max_unit_price))))

    # Gera o parâmetro de saída estruturada (json_schema strict) enviado à OpenRouter.
    @classmethod
    def response_format(cls) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "name": "requisition_draft",
            "strict": True,
            "schema": cls.model_json_schema(),
        }
