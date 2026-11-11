from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


# Regra que recusa itens com quantidade menor que 1
class PositiveQuantityRule(GroundingRule):
    # Devolve o motivo da recusa se a quantidade não for positiva
    def violation(self, candidate: GroundingCandidate) -> str | None:
        if candidate.quantity >= 1:
            return None
        return f"Quantidade inválida ({candidate.quantity}) para {candidate.snapshot.title}."
