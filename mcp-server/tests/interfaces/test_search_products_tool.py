import pytest
from mcp import Client

from tests.fakes.tool_result_reader import ToolResultReader

pytestmark = pytest.mark.anyio


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


async def test_returns_empty_list_when_nothing_matches(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": "ferrari"})

    assert result.is_error is False
    assert result.structured_content == {"products": [], "total": 0}


async def test_rejects_empty_term(client: Client) -> None:
    result = await client.call_tool("buscar_produtos", {"termo": ""})

    assert result.is_error is True


async def test_is_tool_error_when_catalog_is_unavailable(unavailable_client: Client) -> None:
    result = await unavailable_client.call_tool("buscar_produtos", {"termo": "laptop"})

    assert result.is_error is True
    assert "Catálogo indisponível" in ToolResultReader.text(result)
