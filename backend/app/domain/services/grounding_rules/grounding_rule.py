from abc import ABC, abstractmethod

from app.schemas.grounding.grounding_candidate import GroundingCandidate


# Contrato (Strategy) de uma regra de negócio aplicada a cada item candidato
class GroundingRule(ABC):
    @abstractmethod
    def violation(self, candidate: GroundingCandidate) -> str | None:
        """Motivo em pt-BR pelo qual o item não pode entrar na requisição, ou None se ele passa."""
