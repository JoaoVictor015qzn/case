from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.server import MCPServer

from catalog_mcp.application.get_product_detail_use_case import GetProductDetailUseCase
from catalog_mcp.application.search_products_use_case import SearchProductsUseCase
from catalog_mcp.application.submit_requisition_use_case import SubmitRequisitionUseCase
from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.domain.ports.requisition_registry import RequisitionRegistry
from catalog_mcp.interfaces.mcp.errors.catalog_error_translator import CatalogErrorTranslator
from catalog_mcp.interfaces.mcp.routes.health_route import HealthRoute
from catalog_mcp.interfaces.mcp.tools.create_requisition_tool import CreateRequisitionTool
from catalog_mcp.interfaces.mcp.tools.mcp_tool import McpTool
from catalog_mcp.interfaces.mcp.tools.product_detail_tool import ProductDetailTool
from catalog_mcp.interfaces.mcp.tools.search_products_tool import SearchProductsTool

# Assinatura do lifespan aceito pelo MCPServer (abre/fecha recursos do servidor).
Lifespan = Callable[[MCPServer], AbstractAsyncContextManager[Any]]


# Monta o servidor MCP do Catálogo: registra as três tools e a rota de health.
class CatalogMcpServerFactory:
    NAME = "catalogo-produtos"
    # Instruções enviadas ao cliente MCP: catálogo em inglês, preços em USD.
    INSTRUCTIONS = (
        "Catálogo de produtos da DummyJSON. O catálogo é em inglês: busque com termos em inglês "
        "(ex.: 'laptop', 'smartphone'). Preços em USD. criar_requisicao grava a requisição."
    )

    # Recebe os ports já implementados e o lifespan opcional do composition root.
    def __init__(
        self,
        catalog: ProductCatalog,
        registry: RequisitionRegistry,
        lifespan: Lifespan | None = None,
    ) -> None:
        self._catalog = catalog
        self._registry = registry
        self._lifespan = lifespan

    # Cria o MCPServer e registra nele cada tool e a rota GET /health.
    def create(self) -> MCPServer:
        server = MCPServer(self.NAME, instructions=self.INSTRUCTIONS, lifespan=self._lifespan)
        for tool in self._build_tools():
            tool.register(server)
        HealthRoute().register(server)
        return server

    # Instancia as tools com seus casos de uso e um tradutor de erros compartilhado.
    def _build_tools(self) -> list[McpTool]:
        errors = CatalogErrorTranslator()
        return [
            SearchProductsTool(SearchProductsUseCase(self._catalog), errors),
            ProductDetailTool(GetProductDetailUseCase(self._catalog), errors),
            CreateRequisitionTool(SubmitRequisitionUseCase(self._catalog, self._registry), errors),
        ]
