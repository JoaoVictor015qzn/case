from typing import Self

from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.draft_item import DraftItem
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.agent.requisition_draft import RequisitionDraft
from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.product.product_snapshot import ProductSnapshot


class AgentRunBuilder:
    """Monta AgentRun para testes: produtos observados nas tools + rascunho do LLM."""

    def __init__(self) -> None:
        self._observed: dict[int, ProductSnapshot] = {}
        self._items: list[DraftItem] = []
        self._status = DraftStatus.COMPLETE
        self._max_unit_price: float | None = None
        self._missing: list[str] = []
        self._message = "Requisição montada."
        self._tool_calls: list[ToolCallTrace] = []

    def observed(self, *snapshots: ProductSnapshot) -> Self:
        self._observed.update({snapshot.product_id: snapshot for snapshot in snapshots})
        return self

    def item(self, product_id: int, quantity: int) -> Self:
        self._items.append(DraftItem(product_id=product_id, quantity=quantity, reason="teste"))
        return self

    def status(self, status: DraftStatus) -> Self:
        self._status = status
        return self

    def max_unit_price(self, value: float) -> Self:
        self._max_unit_price = value
        return self

    def missing(self, *missing: str) -> Self:
        self._missing.extend(missing)
        return self

    def tool_call(self, name: str, is_error: bool = False) -> Self:
        self._tool_calls.append(
            ToolCallTrace(name=name, arguments={}, is_error=is_error, duration_ms=1)
        )
        return self

    def build(self) -> AgentRun:
        draft = RequisitionDraft(
            status=self._status,
            max_unit_price=self._max_unit_price,
            items=self._items,
            missing=self._missing,
            message=self._message,
        )
        return AgentRun(
            draft=draft, observed_products=self._observed, tool_calls=tuple(self._tool_calls)
        )
