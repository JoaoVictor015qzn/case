from app.domain.services.grounding_rules.grounding_rule import GroundingRule
from app.schemas.grounding.grounding_candidate import GroundingCandidate


# Regra que exige a quantidade mínima de compra definida no catálogo
class MinimumOrderQuantityRule(GroundingRule):
    # Devolve o motivo da recusa se a quantidade pedida fica abaixo do mínimo
    def violation(self, candidate: GroundingCandidate) -> str | None:
        snapshot = candidate.snapshot
        if candidate.quantity >= snapshot.minimum_order_quantity:
            return None
        return (
            f"{snapshot.title} exige compra mínima de {snapshot.minimum_order_quantity} "
            f"unidades (pedido: {candidate.quantity})."
        )
