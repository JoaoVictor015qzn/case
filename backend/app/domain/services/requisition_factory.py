from collections.abc import Sequence

from app.schemas.requisition.requisition import Requisition
from app.schemas.requisition.requisition_item import RequisitionItem
from app.schemas.requisition.requisition_registration import RequisitionRegistration
from app.schemas.requisition.requisition_status import RequisitionStatus


class RequisitionFactory:
    """Monta o agregado Requisition a partir de itens já aprovados pelo grounding."""

    # Cria a requisição com os itens aprovados e os dados do registro
    def create(
        self, registration: RequisitionRegistration, items: Sequence[RequisitionItem]
    ) -> Requisition:
        # Parcial se o agente apontou algo que faltou; senão, completa
        status = RequisitionStatus.PARTIAL if registration.missing else RequisitionStatus.COMPLETE
        return Requisition(
            request_text=registration.request_text,
            status=status,
            items=tuple(items),
            agent_message=registration.message,
            missing=registration.missing,
            idempotency_key=registration.idempotency_key,
        )
