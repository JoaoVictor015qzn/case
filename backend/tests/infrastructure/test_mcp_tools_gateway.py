import pytest

from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.infrastructure.mcp.mcp_tools_gateway import McpToolsGateway
from tests.fakes.fake_catalog_mcp_server import FakeCatalogMcpServer

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio

# Porta 9 (discard) local: ninguém escuta, então a conexão MCP falha rápido.
UNREACHABLE_URL = "http://127.0.0.1:9/mcp"


# Cria gateways MCP de teste.
class GatewayFactory:
    # Gateway ligado em memória ao servidor MCP falso, sem rede.
    @staticmethod
    def in_memory() -> McpToolsGateway:
        return McpToolsGateway(FakeCatalogMcpServer().create(), timeout_s=5)


# Lista as tools do servidor com nome, descrição e schema de entrada.
async def test_lists_tools_with_their_input_schema() -> None:
    async with GatewayFactory.in_memory() as gateway:
        tools = {tool.name: tool for tool in await gateway.list_tools()}

    assert set(tools) == {"buscar_produtos", "quebrada"}
    assert tools["buscar_produtos"].description == "Busca produtos no catálogo."
    assert "termo" in str(tools["buscar_produtos"].input_schema["properties"])


# Chamar uma tool devolve o texto produzido pelo servidor.
async def test_calls_a_tool() -> None:
    async with GatewayFactory.in_memory() as gateway:
        result = await gateway.call_tool("buscar_produtos", {"termo": "laptop"})

    assert result.is_error is False
    assert "buscou laptop" in result.text


# Falha da tool volta como resultado com is_error, para o modelo poder reagir.
async def test_tool_failure_is_a_result_not_an_exception() -> None:
    async with GatewayFactory.in_memory() as gateway:
        result = await gateway.call_tool("quebrada", {"termo": "laptop"})

    assert result.is_error is True
    assert "Catálogo indisponível" in result.text


# Servidor MCP inalcançável vira ToolsUnavailableError ao abrir a sessão.
async def test_unreachable_server_is_tools_unavailable() -> None:
    with pytest.raises(ToolsUnavailableError):
        async with McpToolsGateway(UNREACHABLE_URL, timeout_s=2):
            pass


# Erros levantados dentro do bloco async with não são trocados pelo gateway.
async def test_errors_inside_the_block_keep_their_type() -> None:
    with pytest.raises(LLMTimeoutError):
        async with GatewayFactory.in_memory():
            raise LLMTimeoutError("demorou")
