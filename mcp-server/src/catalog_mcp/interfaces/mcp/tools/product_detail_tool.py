from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from catalog_mcp.application.get_product_detail_use_case import GetProductDetailUseCase
from catalog_mcp.domain.errors.catalog_error import CatalogError
from catalog_mcp.interfaces.mcp.errors.catalog_error_translator import CatalogErrorTranslator
from catalog_mcp.interfaces.mcp.tools.mcp_tool import McpTool
from catalog_mcp.schemas.tools.product_detail import ProductDetail
from catalog_mcp.schemas.tools.tool_arguments import ProductId


# Tool MCP detalhar_produto: devolve preço, estoque e dados de um produto pelo id.
class ProductDetailTool(McpTool):
    NAME = "detalhar_produto"
    TITLE = "Detalhar produto"

    # Recebe o caso de uso de detalhe e o tradutor de erros de domínio para ToolError.
    def __init__(self, use_case: GetProductDetailUseCase, errors: CatalogErrorTranslator) -> None:
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

    async def execute(self, id: ProductId) -> ProductDetail:
        """Detalha um produto pelo id: preço unitário (USD), estoque, quantidade mínima, marca e descrição.

        Use para confirmar preço e estoque antes de incluir o produto numa requisição.
        """
        try:
            return await self._use_case.execute(id)
        except CatalogError as exc:
            raise self._errors.to_tool_error(exc) from exc
