from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


class BudgetRule(GroundingRule):
    def violation(self, candidate: GroundingCandidate) -> str | None:
        budget = candidate.budget
        price = candidate.snapshot.unit_price
        if budget is None or budget.allows(price):
            return None
        return (
            f"{candidate.snapshot.title} custa {price.display()}, acima do orçamento de "
            f"{budget.max_unit_price.display()} por unidade."
        )
