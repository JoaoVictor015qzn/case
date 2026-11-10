from mcp.server.mcpserver.exceptions import ToolError

from catalog_mcp.domain.errors.catalog_error import CatalogError
from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError


class CatalogErrorTranslator:
    """Traduz erros de domínio em ToolError, que o modelo lê e usa para decidir o próximo passo."""

    UNAVAILABLE_TEMPLATE = (
        "Catálogo indisponível: {reason}. Não invente produtos; "
        "informe ao usuário que o catálogo está indisponível no momento."
    )

    def to_tool_error(self, error: CatalogError) -> ToolError:
        if isinstance(error, CatalogUnavailableError):
            return ToolError(self.UNAVAILABLE_TEMPLATE.format(reason=error))
        return ToolError(str(error))
