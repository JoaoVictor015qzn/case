from collections.abc import Sequence

from app.domain.services.grounding_rules.budget_rule import BudgetRule
from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.domain.services.grounding_rules.minimum_order_quantity_rule import (
    MinimumOrderQuantityRule,
)
from app.domain.services.grounding_rules.positive_quantity_rule import PositiveQuantityRule
from app.domain.services.grounding_rules.stock_rule import StockRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate
from app.schemas.grounding.grounding_result import GroundingResult
from app.schemas.requisition.requisition_item import RequisitionItem


class GroundingValidator:
    """Anti-invenção: aplica as regras de negócio sobre os dados reais do catálogo.

    Preço e título vêm do snapshot lido do catálogo; o que o LLM escreveu sobre eles é ignorado.
    """

    # Usa as regras injetadas ou, por padrão, quantidade, estoque, pedido mínimo e orçamento
    def __init__(self, rules: Sequence[GroundingRule] | None = None) -> None:
        self._rules = rules or (
            PositiveQuantityRule(),
            StockRule(),
            MinimumOrderQuantityRule(),
            BudgetRule(),
        )

    # Separa os candidatos em itens aceitos e motivos de recusa
    def validate(self, candidates: Sequence[GroundingCandidate]) -> GroundingResult:
        accepted: list[RequisitionItem] = []
        rejections: list[str] = []
        # Item com violação vira recusa; sem violação vira item com dados do catálogo
        for candidate in candidates:
            violations = self._violations(candidate)
            if violations:
                rejections.extend(violations)
            else:
                accepted.append(
                    RequisitionItem.from_snapshot(candidate.snapshot, candidate.quantity)
                )
        return GroundingResult(accepted=tuple(accepted), rejections=tuple(rejections))

    # Aplica todas as regras ao candidato e junta as mensagens de violação
    def _violations(self, candidate: GroundingCandidate) -> list[str]:
        return [
            violation
            for rule in self._rules
            if (violation := rule.violation(candidate)) is not None
        ]
