import pytest
from mcp import Client

from tests.fakes.tool_result_reader import ToolResultReader

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# A busca devolve os produtos encontrados com preço, estoque e pedido mínimo.
async def test_returns_matching_products_with_price_and_stock(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": "laptop"})

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["total"] == 2
    assert result.structured_content["products"][0] == {
        "id": 78,
        "title": "Apple MacBook Pro 14 Inch Space Grey",
        "category": "laptops",
        "price": {"amount": "1999.99", "currency": "USD"},
        "stock": 24,
        "minimum_order_quantity": 1,
        "availability_status": "In Stock",
    }


# Busca sem resultado devolve lista vazia, sem erro.
async def test_returns_empty_list_when_nothing_matches(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": "ferrari"})

    assert result.is_error is False
    assert result.structured_content == {"products": [], "total": 0}


# Com categoria, o termo filtra os produtos da categoria pelo título ou marca.
async def test_category_search_filters_by_term_in_title_or_brand(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": "lenovo", "categoria": "laptops"})

    assert result.structured_content is not None
    assert [product["id"] for product in result.structured_content["products"]] == [81]


# Com categoria e termo sem correspondência, devolve a categoria inteira.
async def test_category_search_returns_whole_category_when_term_does_not_match(
    client: Client,
) -> None:
    arguments = {"termo": "ultrabook", "categoria": "laptops"}

    result = await client.call_tool("buscar_produtos", arguments)

    assert result.structured_content is not None
    assert [product["id"] for product in result.structured_content["products"]] == [78, 81]


# Categoria fora da lista do catálogo é recusada como erro de tool.
async def test_rejects_category_outside_the_catalog(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": "ferrari", "categoria": "cars"})

    assert result.is_error is True


# Termo vazio é recusado como erro de tool.
async def test_rejects_empty_term(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": ""})

    assert result.is_error is True


# Catálogo fora do ar vira erro de tool com mensagem "Catálogo indisponível".
async def test_is_tool_error_when_catalog_is_unavailable(unavailable_client: Client) -> None:
    result = await unavailable_client.call_tool("buscar_produtos", {"termo": "laptop"})

    assert result.is_error is True
    assert "Catálogo indisponível" in ToolResultReader.text(result)
