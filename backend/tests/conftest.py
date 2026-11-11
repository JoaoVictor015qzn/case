import pytest


# Roda os testes assíncronos do anyio somente sobre asyncio.
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
