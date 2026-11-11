from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


class StockRule(GroundingRule):
    def violation(self, candidate: GroundingCandidate) -> str | None:
        snapshot = candidate.snapshot
        if candidate.quantity <= snapshot.stock:
            return None
        return (
            f"Estoque insuficiente de {snapshot.title}: "
            f"pedido {candidate.quantity}, disponível {snapshot.stock}."
        )
