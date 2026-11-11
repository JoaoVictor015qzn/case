from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.grounding.grounding_result import GroundingResult
from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_status import RequisitionStatus


class RequisitionFactory:
    """Monta o agregado Requisition a partir do rascunho já verificado pelo grounding."""

    NOTHING_FOUND = "O agente não encontrou produtos do catálogo que atendam o pedido."
    ADJUSTED_NOTICE = (
        "Parte dos itens propostos pelo agente não passou na verificação do catálogo "
        "e foi descartada; veja o que falta."
    )

    def create(
        self,
        request_text: str,
        run: AgentRun,
        grounding: GroundingResult,
        idempotency_key: str | None = None,
    ) -> Requisition:
        missing = tuple(run.draft.missing) + grounding.rejections
        if not grounding.has_accepted_items:
            raise RequisitionNotFulfillableError(
                missing=missing or (self.NOTHING_FOUND,),
                agent_message=run.draft.message,
                tool_calls=run.tool_calls,
            )
        return Requisition(
            request_text=request_text,
            status=self._status(run, missing),
            items=grounding.accepted,
            agent_message=self._message(run, grounding),
            missing=missing,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _status(run: AgentRun, missing: tuple[str, ...]) -> RequisitionStatus:
        if missing or run.draft.status is not DraftStatus.COMPLETE:
            return RequisitionStatus.PARTIAL
        return RequisitionStatus.COMPLETE

    def _message(self, run: AgentRun, grounding: GroundingResult) -> str:
        if grounding.is_clean:
            return run.draft.message
        return self.ADJUSTED_NOTICE
