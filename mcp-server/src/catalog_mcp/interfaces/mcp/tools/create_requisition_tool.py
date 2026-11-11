from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from catalog_mcp.application.submit_requisition_use_case import SubmitRequisitionUseCase
from catalog_mcp.domain.errors.catalog_error import CatalogError
from catalog_mcp.interfaces.mcp.errors.catalog_error_translator import CatalogErrorTranslator
from catalog_mcp.interfaces.mcp.tools.mcp_tool import McpTool
from catalog_mcp.schemas.tools.created_requisition_result import CreatedRequisitionResult
from catalog_mcp.schemas.tools.tool_arguments import (
    AgentMessage,
    IdempotencyKey,
    MaxUnitPrice,
    MissingItems,
    RequestText,
    RequisitionItems,
)


# Tool MCP criar_requisicao: grava a requisição no backend com dados reais do catálogo.
class CreateRequisitionTool(McpTool):
    NAME = "criar_requisicao"
    TITLE = "Criar requisição"

    # Recebe o caso de uso de envio e o tradutor de erros de domínio para ToolError.
    def __init__(self, use_case: SubmitRequisitionUseCase, errors: CatalogErrorTranslator) -> None:
        self._use_case = use_case
        self._errors = errors

    # Registra a tool como escrita não destrutiva e idempotente (pela chave de idempotência).
    def register(self, server: MCPServer) -> None:
        server.add_tool(
            self.execute,
            name=self.NAME,
            title=self.TITLE,
            annotations=ToolAnnotations(
                read_only_hint=False,
                destructive_hint=False,
                idempotent_hint=True,
                open_world_hint=False,
            ),
        )

    async def execute(
        self,
        items: RequisitionItems,
        missing: MissingItems,
        message: AgentMessage,
        max_unit_price: MaxUnitPrice,
        request_text: RequestText,
        idempotency_key: IdempotencyKey,
    ) -> CreatedRequisitionResult:
        """Grava a requisição de compra com os produtos escolhidos. Chame uma única vez, no fim.

        Preço, título e estoque são lidos do catálogo pelo sistema; informe só id e quantidade.
        Se a requisição for recusada (ex.: quantidade acima do estoque), nada é gravado: corrija
        e chame de novo, ou mova o item para `missing`. Não chame se nada do pedido existir.
        """
        # Erros de domínio viram ToolError com instruções para o modelo decidir o próximo passo.
        try:
            return await self._use_case.execute(
                items,
                request_text=request_text,
                idempotency_key=idempotency_key,
                missing=missing,
                message=message,
                max_unit_price=max_unit_price,
            )
        except CatalogError as exc:
            raise self._errors.to_tool_error(exc) from exc
