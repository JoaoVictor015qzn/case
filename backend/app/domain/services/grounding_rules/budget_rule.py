from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


# Regra que recusa itens com preço unitário acima do orçamento do pedido
class BudgetRule(GroundingRule):
    # Devolve o motivo da recusa se o preço do catálogo estoura o orçamento
    def violation(self, candidate: GroundingCandidate) -> str | None:
        budget = candidate.budget
        price = candidate.snapshot.unit_price
        # Sem orçamento informado ou preço dentro do limite: item passa
        if budget is None or budget.allows(price):
            return None
        return (
            f"{candidate.snapshot.title} custa {price.display()}, acima do orçamento de "
            f"{budget.max_unit_price.display()} por unidade."
        )
