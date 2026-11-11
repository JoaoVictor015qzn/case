from mcp.types import CallToolResult, TextContent


# Utilitário para ler o resultado de uma tool MCP nos asserts.
class ToolResultReader:
    # Junta o texto de todos os blocos TextContent do resultado.
    @staticmethod
    def text(result: CallToolResult) -> str:
        return " ".join(c.text for c in result.content if isinstance(c, TextContent))
