import pytest

from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from tests.fakes.scripted_transport import ScriptedTransport

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# Um 503 transitório é repetido e a resposta seguinte (200) é devolvida.
async def test_retries_transient_failure_and_returns_next_response() -> None:
    transport = ScriptedTransport(
        ScriptedTransport.respond(503), ScriptedTransport.respond(200, {})
    )

    response = await transport.http_client(max_attempts=3).get("/products/1")

    assert response.status_code == 200
    assert len(transport.requests) == 2


# Timeout persistente esgota as tentativas e vira CatalogUnavailableError.
async def test_gives_up_after_max_attempts_on_timeout() -> None:
    transport = ScriptedTransport(ScriptedTransport.time_out())

    with pytest.raises(CatalogUnavailableError, match="a tempo"):
        await transport.http_client(max_attempts=3).get("/products/1")
    assert len(transport.requests) == 3


# Conexão recusada vira CatalogUnavailableError com mensagem clara.
async def test_connection_error_becomes_catalog_unavailable() -> None:
    transport = ScriptedTransport(ScriptedTransport.refuse_connection())

    with pytest.raises(CatalogUnavailableError, match="conectar"):
        await transport.http_client().get("/products/1")


# Erros 4xx não são repetidos: uma única chamada e a resposta é devolvida.
async def test_does_not_retry_client_errors() -> None:
    transport = ScriptedTransport(ScriptedTransport.respond(404))

    response = await transport.http_client(max_attempts=3).get("/products/999")

    assert response.status_code == 404
    assert len(transport.requests) == 1
