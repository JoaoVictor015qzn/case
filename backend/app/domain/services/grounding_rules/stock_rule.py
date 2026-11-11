from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


# Regra que recusa itens com quantidade maior que o estoque disponível
class StockRule(GroundingRule):
    # Devolve o motivo da recusa se a quantidade pedida passa do estoque
    def violation(self, candidate: GroundingCandidate) -> str | None:
        snapshot = candidate.snapshot
        if candidate.quantity <= snapshot.stock:
            return None
        return (
            f"Estoque insuficiente de {snapshot.title}: "
            f"pedido {candidate.quantity}, disponível {snapshot.stock}."
        )
