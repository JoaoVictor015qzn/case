from collections import Counter
from collections.abc import Sequence

from app.domain.services.grounding_rules.budget_rule import BudgetRule
from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.domain.services.grounding_rules.minimum_order_quantity_rule import (
    MinimumOrderQuantityRule,
)
from app.domain.services.grounding_rules.positive_quantity_rule import PositiveQuantityRule
from app.domain.services.grounding_rules.stock_rule import StockRule
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.draft_item import DraftItem
from app.schemas.grounding.grounding_candidate import GroundingCandidate
from app.schemas.grounding.grounding_result import GroundingResult
from app.schemas.requisition.requisition_item import RequisitionItem


class GroundingValidator:
    """Anti-invenção: só aceita itens com produto observado nesta execução e regras atendidas.

    Preço e título vêm do snapshot da ferramenta; o que o LLM escreveu sobre eles é ignorado.
    """

    NOT_OBSERVED = (
        "Produto {product_id} não foi retornado pelo catálogo nesta consulta e foi descartado."
    )

    def __init__(self, rules: Sequence[GroundingRule] | None = None) -> None:
        self._rules = rules or (
            PositiveQuantityRule(),
            StockRule(),
            MinimumOrderQuantityRule(),
            BudgetRule(),
        )

    def validate(self, run: AgentRun) -> GroundingResult:
        budget = run.draft.budget()
        accepted: list[RequisitionItem] = []
        rejections: list[str] = []
        for product_id, quantity in self._merge_quantities(run.draft.items).items():
            snapshot = run.snapshot_of(product_id)
            if snapshot is None:
                rejections.append(self.NOT_OBSERVED.format(product_id=product_id))
                continue
            candidate = GroundingCandidate(snapshot=snapshot, quantity=quantity, budget=budget)
            violations = self._violations(candidate)
            if violations:
                rejections.extend(violations)
            else:
                accepted.append(RequisitionItem.from_snapshot(snapshot, quantity))
        return GroundingResult(accepted=tuple(accepted), rejections=tuple(rejections))

    def _violations(self, candidate: GroundingCandidate) -> list[str]:
        return [
            violation
            for rule in self._rules
            if (violation := rule.violation(candidate)) is not None
        ]

    @staticmethod
    def _merge_quantities(items: Sequence[DraftItem]) -> Counter[int]:
        quantities: Counter[int] = Counter()
        for item in items:
            quantities[item.product_id] += item.quantity
        return quantities
