from abc import ABC, abstractmethod

from app.schemas.requisition.requisition import Requisition


# Porta de persistência das requisições
class RequisitionRepository(ABC):
    @abstractmethod
    def add(self, requisition: Requisition) -> Requisition:
        """Registra a requisição na transação corrente e a devolve com id e data de criação."""

    @abstractmethod
    def find_by_idempotency_key(self, idempotency_key: str) -> Requisition | None:
        """Busca a requisição criada anteriormente com a mesma chave de idempotência."""

    @abstractmethod
    def list_recent(self, limit: int) -> list[Requisition]:
        """Lista as requisições mais recentes primeiro."""
