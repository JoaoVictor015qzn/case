import pytest

from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.infrastructure.mcp.mcp_tools_gateway import McpToolsGateway
from tests.fakes.fake_catalog_mcp_server import FakeCatalogMcpServer

pytestmark = pytest.mark.anyio

UNREACHABLE_URL = "http://127.0.0.1:9/mcp"


class GatewayFactory:
    @staticmethod
    def in_memory() -> McpToolsGateway:
        return McpToolsGateway(FakeCatalogMcpServer().create(), timeout_s=5)


async def test_lists_tools_with_their_input_schema() -> None:
    async with GatewayFactory.in_memory() as gateway:
        tools = {tool.name: tool for tool in await gateway.list_tools()}

    assert set(tools) == {"buscar_produtos", "quebrada"}
    assert tools["buscar_produtos"].description == "Busca produtos no catálogo."
    assert "termo" in str(tools["buscar_produtos"].input_schema["properties"])


async def test_calls_a_tool() -> None:
    async with GatewayFactory.in_memory() as gateway:
        result = await gateway.call_tool("buscar_produtos", {"termo": "laptop"})

    assert result.is_error is False
    assert "buscou laptop" in result.text


async def test_tool_failure_is_a_result_not_an_exception() -> None:
    async with GatewayFactory.in_memory() as gateway:
        result = await gateway.call_tool("quebrada", {"termo": "laptop"})

    assert result.is_error is True
    assert "Catálogo indisponível" in result.text


async def test_unreachable_server_is_tools_unavailable() -> None:
    with pytest.raises(ToolsUnavailableError):
        async with McpToolsGateway(UNREACHABLE_URL, timeout_s=2):
            pass


async def test_errors_inside_the_block_keep_their_type() -> None:
    with pytest.raises(LLMTimeoutError):
        async with GatewayFactory.in_memory():
            raise LLMTimeoutError("demorou")
