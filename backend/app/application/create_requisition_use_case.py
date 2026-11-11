from asyncer import asyncify

from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.domain.ports.purchasing_agent import PurchasingAgent
from app.domain.ports.unit_of_work import UnitOfWork
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.schemas.requisition.created_requisition import CreatedRequisition
from app.schemas.requisition.requisition import Requisition


class CreateRequisitionUseCase:
    """Pedido em texto -> agente -> grounding -> agregado -> uma transação."""

    def __init__(
        self,
        agent: PurchasingAgent,
        unit_of_work: UnitOfWork,
        validator: GroundingValidator,
        factory: RequisitionFactory,
    ) -> None:
        self._agent = agent
        self._unit_of_work = unit_of_work
        self._validator = validator
        self._factory = factory

    async def execute(
        self, request_text: str, idempotency_key: str | None = None
    ) -> CreatedRequisition:
        if idempotency_key is not None:
            existing = await asyncify(self._find)(idempotency_key)
            if existing is not None:
                return CreatedRequisition(requisition=existing, replayed=True)

        run = await self._agent.run(request_text)
        requisition = self._factory.create(
            request_text, run, self._validator.validate(run), idempotency_key
        )
        try:
            saved = await asyncify(self._save)(requisition)
        except DuplicateIdempotencyKeyError as error:
            return await self._replay_after_race(error)
        return CreatedRequisition(requisition=saved, tool_calls=run.tool_calls)

    async def _replay_after_race(self, error: DuplicateIdempotencyKeyError) -> CreatedRequisition:
        existing = await asyncify(self._find)(error.idempotency_key)
        if existing is None:
            raise error
        return CreatedRequisition(requisition=existing, replayed=True)

    def _find(self, idempotency_key: str) -> Requisition | None:
        with self._unit_of_work as unit_of_work:
            return unit_of_work.requisitions.find_by_idempotency_key(idempotency_key)

    def _save(self, requisition: Requisition) -> Requisition:
        with self._unit_of_work as unit_of_work:
            saved = unit_of_work.requisitions.add(requisition)
            unit_of_work.commit()
            return saved
