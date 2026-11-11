from abc import ABC, abstractmethod

from mcp.server import MCPServer


class McpTool(ABC):
    """Uma ferramenta exposta pelo servidor MCP. Cada implementação se registra no servidor."""

    # Adiciona a tool ao servidor MCP com nome, título e anotações próprias.
    @abstractmethod
    def register(self, server: MCPServer) -> None: ...
