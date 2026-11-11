from collections.abc import AsyncIterator

import pytest
from mcp import Client

from catalog_mcp.interfaces.mcp.server_factory import CatalogMcpServerFactory
from tests.fakes.fake_product_catalog import FakeProductCatalog
from tests.fakes.fake_requisition_registry import FakeRequisitionRegistry
from tests.fakes.sample_products import SampleProducts


# Roda os testes assíncronos do anyio somente sobre asyncio.
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


# Registro falso de requisições, compartilhado com o client para inspecionar envios.
@pytest.fixture
def registry() -> FakeRequisitionRegistry:
    return FakeRequisitionRegistry()


# Client MCP em memória ligado ao servidor real com catálogo falso de amostra.
@pytest.fixture
async def client(registry: FakeRequisitionRegistry) -> AsyncIterator[Client]:
    catalog = FakeProductCatalog(SampleProducts.all())
    server = CatalogMcpServerFactory(catalog, registry).create()
    async with Client(server, raise_exceptions=True) as connected:
        yield connected


# Client MCP cujo catálogo simula a DummyJSON fora do ar.
@pytest.fixture
async def unavailable_client() -> AsyncIterator[Client]:
    catalog = FakeProductCatalog([], unavailable=True)
    server = CatalogMcpServerFactory(catalog, FakeRequisitionRegistry()).create()
    async with Client(server, raise_exceptions=True) as connected:
        yield connected
