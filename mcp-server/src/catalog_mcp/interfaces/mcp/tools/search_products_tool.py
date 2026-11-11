from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from catalog_mcp.application.search_products_use_case import SearchProductsUseCase
from catalog_mcp.domain.errors.catalog_error import CatalogError
from catalog_mcp.interfaces.mcp.errors.catalog_error_translator import CatalogErrorTranslator
from catalog_mcp.interfaces.mcp.tools.mcp_tool import McpTool
from catalog_mcp.schemas.tools.search_products_result import SearchProductsResult
from catalog_mcp.schemas.tools.tool_arguments import SearchCategory, SearchTerm


# Tool MCP buscar_produtos: busca no catálogo por termo, com filtro opcional de categoria.
class SearchProductsTool(McpTool):
    NAME = "buscar_produtos"
    TITLE = "Buscar produtos"

    # Recebe o caso de uso de busca e o tradutor de erros de domínio para ToolError.
    def __init__(self, use_case: SearchProductsUseCase, errors: CatalogErrorTranslator) -> None:
        self._use_case = use_case
        self._errors = errors

    # Registra a tool como somente leitura sobre um sistema externo (DummyJSON).
    def register(self, server: MCPServer) -> None:
        server.add_tool(
            self.execute,
            name=self.NAME,
            title=self.TITLE,
            annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
        )

    async def execute(
        self, termo: SearchTerm, categoria: SearchCategory = None
    ) -> SearchProductsResult:
        """Busca produtos no catálogo por termo (título, descrição e categoria).

        Retorna id, título, categoria, preço unitário (USD) e estoque de cada produto.
        Sem categoria, lista vazia significa que nenhum produto corresponde ao termo: tente um
        sinônimo em inglês ou informe a categoria. Com categoria, o termo filtra por título ou
        marca; se nenhum produto da categoria tiver o termo, vêm todos os produtos dela.
        """
        try:
            return await self._use_case.execute(termo, categoria)
        except CatalogError as exc:
            raise self._errors.to_tool_error(exc) from exc
