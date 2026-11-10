from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.server import MCPServer

from catalog_mcp.application.get_product_detail_use_case import GetProductDetailUseCase
from catalog_mcp.application.search_products_use_case import SearchProductsUseCase
from catalog_mcp.domain.ports.product_catalog import ProductCatalog
from catalog_mcp.interfaces.mcp.errors.catalog_error_translator import CatalogErrorTranslator
from catalog_mcp.interfaces.mcp.routes.health_route import HealthRoute
from catalog_mcp.interfaces.mcp.tools.mcp_tool import McpTool
from catalog_mcp.interfaces.mcp.tools.product_detail_tool import ProductDetailTool
from catalog_mcp.interfaces.mcp.tools.search_products_tool import SearchProductsTool

Lifespan = Callable[[MCPServer], AbstractAsyncContextManager[Any]]


class CatalogMcpServerFactory:
    NAME = "catalogo-produtos"
    INSTRUCTIONS = (
        "Catálogo de produtos da DummyJSON. O catálogo é em inglês: busque com termos em inglês "
        "(ex.: 'laptop', 'smartphone'). Preços em USD."
    )

    def __init__(self, catalog: ProductCatalog, lifespan: Lifespan | None = None) -> None:
        self._catalog = catalog
        self._lifespan = lifespan

    def create(self) -> MCPServer:
        server = MCPServer(self.NAME, instructions=self.INSTRUCTIONS, lifespan=self._lifespan)
        for tool in self._build_tools():
            tool.register(server)
        HealthRoute().register(server)
        return server

    def _build_tools(self) -> list[McpTool]:
        errors = CatalogErrorTranslator()
        return [
            SearchProductsTool(SearchProductsUseCase(self._catalog), errors),
            ProductDetailTool(GetProductDetailUseCase(self._catalog), errors),
        ]
