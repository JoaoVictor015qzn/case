from types import TracebackType
from typing import Self

from pydantic import JsonValue

from app.domain.ports.catalog_tools_gateway import CatalogToolsGateway
from app.schemas.tools.tool_definition import ToolDefinition
from app.schemas.tools.tool_result import ToolResult
from tests.fakes.catalog_tool_results import CatalogToolResults


class FakeCatalogToolsGateway(CatalogToolsGateway):
    def __init__(self, results: dict[str, ToolResult] | None = None) -> None:
        self._results = results or {}
        self.calls: list[tuple[str, dict[str, JsonValue]]] = []
        self.closed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.closed = True

    async def list_tools(self) -> list[ToolDefinition]:
        return [CatalogToolResults.SEARCH_TOOL]

    async def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> ToolResult:
        self.calls.append((name, arguments))
        return self._results.get(name, CatalogToolResults.error(f"Unknown tool: {name}"))
