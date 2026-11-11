from mcp.server.mcpserver.exceptions import ToolError

from catalog_mcp.domain.errors.catalog_error import CatalogError
from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from catalog_mcp.domain.errors.requisition_registry_unavailable_error import (
    RequisitionRegistryUnavailableError,
)
from catalog_mcp.domain.errors.requisition_rejected_error import RequisitionRejectedError


class CatalogErrorTranslator:
    """Traduz erros de domínio em ToolError, que o modelo lê e usa para decidir o próximo passo."""

    # Mensagens que orientam o modelo: não inventar produtos nem dizer que gravou sem gravar.
    UNAVAILABLE_TEMPLATE = (
        "Catálogo indisponível: {reason}. Não invente produtos; "
        "informe ao usuário que o catálogo está indisponível no momento."
    )
    REJECTED_TEMPLATE = (
        "Requisição recusada, nada foi gravado: {reason} Corrija os itens e chame "
        "criar_requisicao de novo, ou mova o item para missing."
    )
    REGISTRY_UNAVAILABLE_TEMPLATE = (
        "Não foi possível gravar a requisição: {reason}. Não diga ao usuário que ela foi criada."
    )

    # Escolhe o template pelo tipo do erro; os demais (ex.: não encontrado) vão com a mensagem crua.
    def to_tool_error(self, error: CatalogError) -> ToolError:
        if isinstance(error, CatalogUnavailableError):
            return ToolError(self.UNAVAILABLE_TEMPLATE.format(reason=error))
        if isinstance(error, RequisitionRejectedError):
            return ToolError(self.REJECTED_TEMPLATE.format(reason=error))
        if isinstance(error, RequisitionRegistryUnavailableError):
            return ToolError(self.REGISTRY_UNAVAILABLE_TEMPLATE.format(reason=error))
        return ToolError(str(error))
