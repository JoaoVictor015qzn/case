import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from catalog_mcp.infrastructure.dummyjson.dummyjson_http_client import DummyJsonHttpClient
from catalog_mcp.infrastructure.dummyjson.dummyjson_product_catalog import DummyJsonProductCatalog
from catalog_mcp.infrastructure.dummyjson.dummyjson_product_mapper import DummyJsonProductMapper
from catalog_mcp.interfaces.mcp.server_factory import CatalogMcpServerFactory
from catalog_mcp.schemas.settings.settings import Settings


class Application:
    """Composition root: o único lugar que decide qual implementação entra em cada port."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http_client = DummyJsonHttpClient.from_settings(settings)

    def build_server(self) -> MCPServer:
        catalog = DummyJsonProductCatalog(
            self._http_client, DummyJsonProductMapper(), self._settings.search_limit
        )
        return CatalogMcpServerFactory(catalog, lifespan=self._lifespan).create()

    def run(self) -> None:
        logging.basicConfig(
            level=self._settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        self.build_server().run(
            transport="streamable-http",
            host=self._settings.host,
            port=self._settings.port,
            stateless_http=True,
            transport_security=TransportSecuritySettings(
                allowed_hosts=self._settings.allowed_hosts
            ),
        )

    @asynccontextmanager
    async def _lifespan(self, _server: MCPServer) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            await self._http_client.aclose()


if __name__ == "__main__":
    Application(Settings()).run()
