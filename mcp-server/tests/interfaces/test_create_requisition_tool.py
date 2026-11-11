from decimal import Decimal

import pytest
from mcp import Client

from catalog_mcp.interfaces.mcp.server_factory import CatalogMcpServerFactory
from tests.fakes.fake_product_catalog import FakeProductCatalog
from tests.fakes.fake_requisition_registry import FakeRequisitionRegistry
from tests.fakes.sample_products import SampleProducts
from tests.fakes.tool_result_reader import ToolResultReader

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# Monta os argumentos de criar_requisicao a partir de pares (product_id, quantidade).
class Arguments:
    # Fixa teto de preço, texto do pedido e chave de idempotência; missing é opcional.
    @staticmethod
    def build(*items: tuple[int, int], missing: list[str] | None = None) -> dict[str, object]:
        return {
            "items": [{"product_id": pid, "quantity": qty} for pid, qty in items],
            "missing": missing or [],
            "message": "Requisição montada.",
            "max_unit_price": 2000,
            "request_text": "2 macbooks",
            "idempotency_key": "chave-1",
        }


# Envia ao backend o preço e estoque do catálogo (não do modelo) e devolve número e total.
async def test_sends_catalog_prices_and_returns_requisition_number(
    client: Client, registry: FakeRequisitionRegistry
) -> None:
    result = await client.call_tool("criar_requisicao", Arguments.build((78, 2)))

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["requisition_id"] == 1
    assert result.structured_content["total"] == {"amount": "3999.98", "currency": "USD"}
    (submission,) = registry.submissions
    assert submission.items[0].unit_price.amount == Decimal("1999.99")
    assert submission.items[0].stock == 24
    assert submission.idempotency_key == "chave-1"
    assert submission.max_unit_price == Decimal("2000")


# O mesmo produto repetido vira um único item com as quantidades somadas.
async def test_merges_repeated_products(client: Client, registry: FakeRequisitionRegistry) -> None:
    await client.call_tool("criar_requisicao", Arguments.build((81, 1), (81, 2)))

    (item,) = registry.submissions[0].items
    assert item.quantity == 3


# Produto inexistente vira erro de tool e nada é enviado ao backend.
async def test_unknown_product_is_tool_error_and_nothing_is_sent(
    client: Client, registry: FakeRequisitionRegistry
) -> None:
    result = await client.call_tool("criar_requisicao", Arguments.build((999, 1)))

    assert result.is_error is True
    assert "Produto 999 não existe" in ToolResultReader.text(result)
    assert registry.submissions == []


# Recusa do backend avisa o modelo que nada foi gravado e repassa o motivo.
async def test_rejection_from_backend_tells_the_model_to_fix_and_retry() -> None:
    registry = FakeRequisitionRegistry(rejection="Estoque insuficiente para o produto 78.")
    server = CatalogMcpServerFactory(FakeProductCatalog(SampleProducts.all()), registry).create()
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool("criar_requisicao", Arguments.build((78, 2)))

    text = ToolResultReader.text(result)
    assert result.is_error is True
    assert "nada foi gravado" in text
    assert "Estoque insuficiente" in text


# Backend fora do ar vira erro de tool que proíbe dizer que a requisição foi criada.
async def test_backend_unavailable_is_tool_error() -> None:
    registry = FakeRequisitionRegistry(unavailable=True)
    server = CatalogMcpServerFactory(FakeProductCatalog(SampleProducts.all()), registry).create()
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool("criar_requisicao", Arguments.build((78, 1)))

    assert result.is_error is True
    assert "Não diga ao usuário que ela foi criada" in ToolResultReader.text(result)


# Lista de itens vazia é recusada na validação dos argumentos.
async def test_rejects_empty_item_list(client: Client) -> None:
    result = await client.call_tool("criar_requisicao", Arguments.build())

    assert result.is_error is True
