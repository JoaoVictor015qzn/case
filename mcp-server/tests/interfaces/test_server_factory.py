import pytest
from mcp import Client

pytestmark = pytest.mark.anyio


async def test_exposes_exactly_the_catalog_tools(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {"buscar_produtos", "detalhar_produto"}


async def test_tools_declare_required_arguments(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert tools["buscar_produtos"].input_schema["required"] == ["termo"]
    assert tools["detalhar_produto"].input_schema["required"] == ["id"]


async def test_tools_are_read_only(client: Client) -> None:
    tools = (await client.list_tools()).tools

    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools)
