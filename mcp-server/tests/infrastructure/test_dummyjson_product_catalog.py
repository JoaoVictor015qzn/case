from decimal import Decimal

import pytest

from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from catalog_mcp.domain.errors.product_not_found_error import ProductNotFoundError
from catalog_mcp.infrastructure.dummyjson.dummyjson_product_catalog import DummyJsonProductCatalog
from catalog_mcp.infrastructure.dummyjson.dummyjson_product_mapper import DummyJsonProductMapper
from catalog_mcp.schemas.product.product_category import ProductCategory
from tests.fakes.scripted_transport import ScriptedTransport

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio

# Produto como a DummyJSON devolve (camelCase, preço float), para testar o mapeamento.
MACBOOK_JSON = {
    "id": 78,
    "title": "Apple MacBook Pro 14 Inch Space Grey",
    "category": "laptops",
    "price": 1999.99,
    "stock": 24,
    "availabilityStatus": "In Stock",
    "minimumOrderQuantity": 2,
    "brand": "Apple",
}


# Monta o catálogo real da DummyJSON sobre o transporte roteirizado.
def build_catalog(transport: ScriptedTransport) -> DummyJsonProductCatalog:
    return DummyJsonProductCatalog(
        transport.http_client(), DummyJsonProductMapper(), search_limit=10
    )


# A busca chama /products/search com o termo e o limite configurado.
async def test_search_sends_term_and_limit() -> None:
    transport = ScriptedTransport(ScriptedTransport.respond(200, {"products": [], "total": 0}))

    await build_catalog(transport).search("laptop")

    request = transport.requests[0]
    assert request.url.path == "/products/search"
    assert request.url.params["q"] == "laptop"
    assert request.url.params["limit"] == "10"


# O JSON em camelCase vira Product com preço Decimal, pedido mínimo e disponibilidade.
async def test_search_maps_camel_case_payload_to_product() -> None:
    payload = {"products": [MACBOOK_JSON], "total": 1}
    transport = ScriptedTransport(ScriptedTransport.respond(200, payload))

    [product] = await build_catalog(transport).search("laptop")

    assert product.price.amount == Decimal("1999.99")
    assert product.minimum_order_quantity == 2
    assert product.availability_status == "In Stock"


# Listar categoria pede a rota da categoria com limit=0 (todos os itens).
async def test_list_category_requests_the_whole_category() -> None:
    payload = {"products": [MACBOOK_JSON], "total": 1}
    transport = ScriptedTransport(ScriptedTransport.respond(200, payload))

    [product] = await build_catalog(transport).list_category(ProductCategory.LAPTOPS)

    request = transport.requests[0]
    assert request.url.path == "/products/category/laptops"
    assert request.url.params["limit"] == "0"
    assert product.id == 78


# HTTP 404 no detalhe vira ProductNotFoundError do domínio.
async def test_get_maps_404_to_product_not_found() -> None:
    transport = ScriptedTransport(ScriptedTransport.respond(404, {"message": "not found"}))

    with pytest.raises(ProductNotFoundError):
        await build_catalog(transport).get(999)


# Resposta 200 com formato inesperado é tratada como catálogo indisponível.
async def test_unexpected_payload_becomes_catalog_unavailable() -> None:
    transport = ScriptedTransport(ScriptedTransport.respond(200, {"unexpected": True}))

    with pytest.raises(CatalogUnavailableError, match="inesperada"):
        await build_catalog(transport).get(78)
