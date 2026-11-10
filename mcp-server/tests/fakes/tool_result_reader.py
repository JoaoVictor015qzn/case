from mcp.types import CallToolResult, TextContent


class ToolResultReader:
    @staticmethod
    def text(result: CallToolResult) -> str:
        return " ".join(c.text for c in result.content if isinstance(c, TextContent))
