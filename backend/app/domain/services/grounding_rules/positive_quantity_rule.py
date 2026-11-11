from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


class PositiveQuantityRule(GroundingRule):
    def violation(self, candidate: GroundingCandidate) -> str | None:
        if candidate.quantity >= 1:
            return None
        return f"Quantidade inválida ({candidate.quantity}) para {candidate.snapshot.title}."
