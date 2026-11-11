from pydantic import BaseModel, ConfigDict

from app.schemas.agent.requisition_draft import RequisitionDraft
from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.product.product_snapshot import ProductSnapshot


class AgentRun(BaseModel):
    """Resultado de uma execução do agente: o rascunho e tudo o que as ferramentas devolveram."""

    model_config = ConfigDict(frozen=True)

    draft: RequisitionDraft
    observed_products: dict[int, ProductSnapshot] = {}
    tool_calls: tuple[ToolCallTrace, ...] = ()

    def snapshot_of(self, product_id: int) -> ProductSnapshot | None:
        return self.observed_products.get(product_id)
