import pytest
from mcp import Client

from tests.fakes.tool_result_reader import ToolResultReader

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# O detalhe devolve preço, marca e pedido mínimo do produto.
async def test_returns_product_details(client: Client) -> None:
    result = await client.call_tool("detalhar_produto", {"id": 78})

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["price"] == {"amount": "1999.99", "currency": "USD"}
    assert result.structured_content["brand"] == "Apple"
    assert result.structured_content["minimum_order_quantity"] == 1


# Id inexistente vira erro de tool dizendo que o produto não existe.
async def test_unknown_id_is_tool_error(client: Client) -> None:
    result = await client.call_tool("detalhar_produto", {"id": 999})

    assert result.is_error is True
    assert "Produto 999 não existe" in ToolResultReader.text(result)


# Id zero ou negativo é recusado na validação dos argumentos.
async def test_rejects_non_positive_id(client: Client) -> None:
    result = await client.call_tool("detalhar_produto", {"id": 0})

    assert result.is_error is True


# Catálogo fora do ar vira erro de tool com mensagem "Catálogo indisponível".
async def test_is_tool_error_when_catalog_is_unavailable(unavailable_client: Client) -> None:
    result = await unavailable_client.call_tool("detalhar_produto", {"id": 78})

    assert result.is_error is True
    assert "Catálogo indisponível" in ToolResultReader.text(result)
