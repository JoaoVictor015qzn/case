from abc import ABC, abstractmethod

from app.schemas.grounding.grounding_candidate import GroundingCandidate


class GroundingRule(ABC):
    @abstractmethod
    def violation(self, candidate: GroundingCandidate) -> str | None:
        """Motivo em pt-BR pelo qual o item não pode entrar na requisição, ou None se ele passa."""
