from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.domain.ports.requisition_repository import RequisitionRepository
from app.schemas.requisition.requisition import Requisition


# Repositório em memória: grava em pendentes e enxerga também o que já teve commit.
class InMemoryRequisitionRepository(RequisitionRepository):
    def __init__(self, committed: list[Requisition]) -> None:
        self._committed = committed
        self.pending: list[Requisition] = []

    # Recusa chave de idempotência repetida e atribui id sequencial.
    def add(self, requisition: Requisition) -> Requisition:
        key = requisition.idempotency_key
        if key is not None and self.find_by_idempotency_key(key) is not None:
            raise DuplicateIdempotencyKeyError(key)
        next_id = len(self._committed) + len(self.pending) + 1
        saved = requisition.with_identity(next_id, requisition.created_at)
        self.pending.append(saved)
        return saved

    # Procura a chave entre as requisições efetivadas e as pendentes.
    def find_by_idempotency_key(self, idempotency_key: str) -> Requisition | None:
        return next(
            (
                requisition
                for requisition in [*self._committed, *self.pending]
                if requisition.idempotency_key == idempotency_key
            ),
            None,
        )

    # Devolve só as efetivadas, das mais novas para as mais antigas.
    def list_recent(self, limit: int) -> list[Requisition]:
        newest_first = sorted(self._committed, key=lambda item: item.created_at, reverse=True)
        return newest_first[:limit]
