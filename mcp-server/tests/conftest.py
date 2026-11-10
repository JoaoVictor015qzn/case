from collections.abc import AsyncIterator

import pytest
from mcp import Client

from catalog_mcp.interfaces.mcp.server_factory import CatalogMcpServerFactory
from tests.fakes.fake_product_catalog import FakeProductCatalog
from tests.fakes.sample_products import SampleProducts


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    server = CatalogMcpServerFactory(FakeProductCatalog(SampleProducts.all())).create()
    async with Client(server, raise_exceptions=True) as connected:
        yield connected


@pytest.fixture
async def unavailable_client() -> AsyncIterator[Client]:
    server = CatalogMcpServerFactory(FakeProductCatalog([], unavailable=True)).create()
    async with Client(server, raise_exceptions=True) as connected:
        yield connected
