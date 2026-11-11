from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.domain.ports.requisition_registry import RequisitionRegistry
from catalog_mcp.schemas.requisition.requisition_submission import RequisitionSubmission
from catalog_mcp.schemas.requisition.requisition_submission_item import RequisitionSubmissionItem
from catalog_mcp.schemas.tools.created_requisition_result import CreatedRequisitionResult
from catalog_mcp.schemas.tools.requisition_item_argument import RequisitionItemArgument


class SubmitRequisitionUseCase:
    """Relê cada produto no catálogo e envia ao backend só dados reais: o modelo escolhe id e qtd."""

    # Recebe o catálogo (preço/estoque reais) e o registro de requisições (backend).
    def __init__(self, catalog: ProductCatalog, registry: RequisitionRegistry) -> None:
        self._catalog = catalog
        self._registry = registry

    # Monta a submissão com dados do catálogo, grava no backend e devolve o resultado da tool.
    async def execute(
        self,
        items: Sequence[RequisitionItemArgument],
        request_text: str,
        idempotency_key: str,
        missing: Sequence[str] = (),
        message: str = "",
        max_unit_price: float | None = None,
    ) -> CreatedRequisitionResult:
        # Teto de preço vira Decimal via str para não herdar imprecisão do float.
        submission = RequisitionSubmission(
            request_text=request_text,
            idempotency_key=idempotency_key,
            items=await self._read_from_catalog(items),
            max_unit_price=None if max_unit_price is None else Decimal(str(max_unit_price)),
            missing=list(missing),
            message=message,
        )
        return CreatedRequisitionResult.from_registration(await self._registry.register(submission))

    # Soma quantidades por produto e relê cada um no catálogo para obter dados reais.
    async def _read_from_catalog(
        self, items: Sequence[RequisitionItemArgument]
    ) -> list[RequisitionSubmissionItem]:
        # Agrupa itens repetidos do mesmo produto numa única linha.
        quantities: Counter[int] = Counter()
        for item in items:
            quantities[item.product_id] += item.quantity
        # Busca cada produto no catálogo e gera o item com preço e estoque atuais.
        return [
            RequisitionSubmissionItem.from_product(await self._catalog.get(product_id), quantity)
            for product_id, quantity in quantities.items()
        ]
