import logging
from types import TracebackType
from typing import Self

import httpx2
from mcp import Client, MCPError
from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import JsonValue

from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.domain.ports.catalog_tools_gateway import CatalogToolsGateway
from app.schemas.tools.tool_definition import ToolDefinition
from app.schemas.tools.tool_result import ToolResult

logger = logging.getLogger(__name__)


class McpToolsGateway(CatalogToolsGateway):
    """Cliente MCP (Streamable HTTP) aberto por execução do agente: o backend segue stateless."""

    CONNECTION_ERRORS = (MCPError, httpx2.HTTPError, OSError)

    def __init__(self, target: str | MCPServer, timeout_s: float) -> None:
        self._target = target
        self._timeout_s = timeout_s
        self._client: Client | None = None

    async def __aenter__(self) -> Self:
        client = Client(self._target, read_timeout_seconds=self._timeout_s)
        try:
            await client.__aenter__()
        except Exception as error:
            raise self._unavailable(error) from error
        self._client = client
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        try:
            await client.__aexit__(exc_type, exc, traceback)
        except BaseExceptionGroup as group:
            # O task group do transporte embrulha o erro do bloco `with`; o original é o que importa.
            if isinstance(exc, Exception):
                raise exc from group
            raise self._unavailable(group) from group

    async def list_tools(self) -> list[ToolDefinition]:
        try:
            listed = await self._connected().list_tools()
        except self.CONNECTION_ERRORS as error:
            raise self._unavailable(error) from error
        return [self._to_definition(tool) for tool in listed.tools]

    async def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> ToolResult:
        try:
            result = await self._connected().call_tool(name, arguments)
        except self.CONNECTION_ERRORS as error:
            raise self._unavailable(error) from error
        return self._to_result(result)

    def _connected(self) -> Client:
        if self._client is None:
            raise RuntimeError("Use o gateway dentro de um bloco `async with`.")
        return self._client

    @staticmethod
    def _to_definition(tool: Tool) -> ToolDefinition:
        return ToolDefinition(
            name=tool.name, description=tool.description or "", input_schema=tool.input_schema
        )

    @staticmethod
    def _to_result(result: CallToolResult) -> ToolResult:
        text = "\n".join(part.text for part in result.content if isinstance(part, TextContent))
        return ToolResult(
            is_error=result.is_error, text=text, structured_content=result.structured_content
        )

    @classmethod
    def _unavailable(cls, error: BaseException) -> ToolsUnavailableError:
        detail = cls._describe(error)
        logger.warning("mcp_unavailable error=%s", detail)
        return ToolsUnavailableError(detail)

    @classmethod
    def _describe(cls, error: BaseException) -> str:
        if isinstance(error, BaseExceptionGroup):
            return "; ".join(cls._describe(inner) for inner in error.exceptions)
        return f"{type(error).__name__}: {error}"
