from asyncer import asyncify

from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.domain.errors.requisition_rejected_error import RequisitionRejectedError
from app.domain.ports.unit_of_work import UnitOfWork
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.grounding.grounding_candidate import GroundingCandidate
from app.schemas.requisition.created_requisition import CreatedRequisition
from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_registration import RequisitionRegistration


class RegisterRequisitionUseCase:
    """Gravação pedida pelo agente via criar_requisicao: grounding -> agregado -> uma transação.

    Se qualquer item violar uma regra, nada é gravado e o motivo volta para o modelo corrigir.
    """

    # Recebe a unidade de trabalho, o validador de grounding e a fábrica do agregado
    def __init__(
        self, unit_of_work: UnitOfWork, validator: GroundingValidator, factory: RequisitionFactory
    ) -> None:
        self._unit_of_work = unit_of_work
        self._validator = validator
        self._factory = factory

    # Valida os itens e grava a requisição, ou recusa sem gravar nada
    async def execute(self, registration: RequisitionRegistration) -> CreatedRequisition:
        # Replay: a chave já foi gravada, devolve a requisição existente
        existing = await asyncify(self._find)(registration.idempotency_key)
        if existing is not None:
            return CreatedRequisition(requisition=existing, replayed=True)

        # Converte cada linha em candidato com o snapshot do catálogo e o orçamento
        candidates = [
            GroundingCandidate(
                snapshot=line.snapshot, quantity=line.quantity, budget=registration.budget
            )
            for line in registration.lines
        ]
        grounding = self._validator.validate(candidates)
        # Qualquer violação recusa a requisição inteira e devolve os motivos ao modelo
        if not grounding.is_clean:
            raise RequisitionRejectedError(grounding.rejections)
        requisition = self._factory.create(registration, grounding.accepted)
        try:
            saved = await asyncify(self._save)(requisition)
        # Corrida: outra gravação usou a mesma chave antes; devolve a que venceu
        except DuplicateIdempotencyKeyError:
            existing = await asyncify(self._find)(registration.idempotency_key)
            if existing is None:
                raise
            return CreatedRequisition(requisition=existing, replayed=True)
        return CreatedRequisition(requisition=saved)

    # Busca no banco a requisição associada à chave de idempotência
    def _find(self, idempotency_key: str) -> Requisition | None:
        with self._unit_of_work as unit_of_work:
            return unit_of_work.requisitions.find_by_idempotency_key(idempotency_key)

    # Grava a requisição e confirma a transação
    def _save(self, requisition: Requisition) -> Requisition:
        with self._unit_of_work as unit_of_work:
            saved = unit_of_work.requisitions.add(requisition)
            unit_of_work.commit()
            return saved
