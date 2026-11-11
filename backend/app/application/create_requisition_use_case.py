from uuid import uuid4

from asyncer import asyncify

from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.domain.errors.requisition_not_saved_error import RequisitionNotSavedError
from app.domain.ports.purchasing_agent import PurchasingAgent
from app.domain.ports.unit_of_work import UnitOfWork
from app.schemas.agent.agent_request import AgentRequest
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.requisition.created_requisition import CreatedRequisition
from app.schemas.requisition.requisition import Requisition


class CreateRequisitionUseCase:
    """Pedido em texto -> agente. Quem grava é o agente, pela tool criar_requisicao.

    A gravação usa a chave de idempotência deste pedido, então basta procurá-la depois do agente.
    """

    # Motivo padrão do 422 quando o agente não informa o que faltou
    NOTHING_FOUND = "O agente não encontrou produtos do catálogo que atendam o pedido."
    # Detalhe técnico do 502: o modelo encerrou sem a requisição ter sido gravada
    NOT_SAVED = "status={status} sem chamada bem-sucedida de criar_requisicao"

    # Recebe o agente de compras e a unidade de trabalho para consultar o banco
    def __init__(self, agent: PurchasingAgent, unit_of_work: UnitOfWork) -> None:
        self._agent = agent
        self._unit_of_work = unit_of_work

    # Processa o pedido em texto e devolve a requisição gravada pelo agente
    async def execute(
        self, request_text: str, idempotency_key: str | None = None
    ) -> CreatedRequisition:
        # Replay: se a Idempotency-Key já gerou requisição, devolve-a sem rodar o agente
        if idempotency_key is not None:
            existing = await asyncify(self._find)(idempotency_key)
            if existing is not None:
                return CreatedRequisition(requisition=existing, replayed=True)

        # Sem chave do cliente, gera uma para a tool criar_requisicao gravar com ela
        key = idempotency_key or uuid4().hex
        run = await self._agent.run(AgentRequest(request_text=request_text, idempotency_key=key))
        # Procura pela chave a requisição que a tool criar_requisicao gravou
        saved = await asyncify(self._find)(key)
        if saved is not None:
            return CreatedRequisition(requisition=saved, tool_calls=run.tool_calls)
        # Nada gravado e nada no catálogo atende o pedido: erro 422 com o que faltou
        if run.draft.status is DraftStatus.UNFULFILLABLE:
            raise RequisitionNotFulfillableError(
                missing=tuple(run.draft.missing) or (self.NOTHING_FOUND,),
                agent_message=run.draft.message,
                tool_calls=run.tool_calls,
            )
        # Nada gravado mas o modelo disse que criou: falha do agente, erro 502
        raise RequisitionNotSavedError(
            self.NOT_SAVED.format(status=run.draft.status.value), run.tool_calls
        )

    # Busca no banco a requisição associada à chave de idempotência
    def _find(self, idempotency_key: str) -> Requisition | None:
        with self._unit_of_work as unit_of_work:
            return unit_of_work.requisitions.find_by_idempotency_key(idempotency_key)
