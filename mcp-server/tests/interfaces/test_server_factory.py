import json

import pytest
from mcp import Client

from catalog_mcp.schemas.product.product_category import ProductCategory

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# O servidor publica exatamente as três tools do case, nem mais nem menos.
async def test_exposes_exactly_the_three_tools(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {"buscar_produtos", "detalhar_produto", "criar_requisicao"}


# O schema de cada tool declara os argumentos obrigatórios esperados pelo modelo.
async def test_tools_declare_required_arguments(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert tools["buscar_produtos"].input_schema["required"] == ["termo"]
    assert tools["detalhar_produto"].input_schema["required"] == ["id"]
    assert set(tools["criar_requisicao"].input_schema["required"]) == {
        "items",
        "missing",
        "message",
        "max_unit_price",
        "request_text",
        "idempotency_key",
    }


# O schema de buscar_produtos enumera todas as categorias válidas do catálogo.
async def test_buscar_produtos_schema_lists_every_catalog_category(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    schema = json.dumps(tools["buscar_produtos"].input_schema)

    assert all(f'"{category}"' in schema for category in ProductCategory)


# Só criar_requisicao fica sem a anotação read-only; as tools de leitura a têm.
async def test_only_criar_requisicao_writes(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    read_only = {
        name for name, tool in tools.items() if tool.annotations and tool.annotations.read_only_hint
    }
    assert read_only == {"buscar_produtos", "detalhar_produto"}
