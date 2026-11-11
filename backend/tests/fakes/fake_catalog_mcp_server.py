from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


class FakeCatalogMcpServer:
    """Servidor MCP em memória para testar o McpToolsGateway sem rede."""

    def search(self, termo: str) -> str:
        """Busca produtos no catálogo."""
        return f"buscou {termo}"

    def broken(self, termo: str) -> str:
        """Ferramenta que sempre falha."""
        raise ToolError(f"Catálogo indisponível ao buscar {termo}.")

    # Registra uma tool que funciona (buscar_produtos) e outra que sempre falha (quebrada).
    def create(self) -> MCPServer:
        server = MCPServer("fake-catalog")
        server.add_tool(self.search, name="buscar_produtos")
        server.add_tool(self.broken, name="quebrada")
        return server
