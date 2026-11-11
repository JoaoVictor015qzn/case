from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from catalog_mcp.domain.errors.requisition_registry_unavailable_error import (
    RequisitionRegistryUnavailableError,
)
from catalog_mcp.domain.errors.requisition_rejected_error import RequisitionRejectedError
from catalog_mcp.infrastructure.backend.backend_requisition_registry import (
    BackendRequisitionRegistry,
)
from catalog_mcp.schemas.requisition.requisition_submission import RequisitionSubmission
from catalog_mcp.schemas.requisition.requisition_submission_item import RequisitionSubmissionItem
from tests.fakes.sample_products import SampleProducts
from tests.fakes.scripted_transport import ScriptedTransport, Step

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio

# Requisição de exemplo enviada ao backend: 2 MacBooks dentro do teto de preço.
SUBMISSION = RequisitionSubmission(
    request_text="2 macbooks",
    idempotency_key="chave-1",
    items=[RequisitionSubmissionItem.from_product(SampleProducts.MACBOOK, 2)],
    max_unit_price=Decimal("2000"),
    missing=[],
    message="ok",
)
# Resposta 201 do endpoint interno do backend para a requisição criada.
CREATED = {
    "requisition": {
        "id": 7,
        "status": "complete",
        "total": {"amount": "3999.98", "currency": "USD"},
    },
    "replayed": False,
}


# Monta o registro real do backend sobre httpx.MockTransport e guarda as requisições.
class RegistryHarness:
    def __init__(self, step: Step) -> None:
        self._step = step
        self.requests: list[httpx.Request] = []
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(self._handle), base_url="http://backend:8000"
        )
        self.registry = BackendRequisitionRegistry(client, SecretStr("token-de-teste-123"))

    # Registra a requisição recebida e responde com o passo configurado.
    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._step(request)


# Envia POST /internal/requisicoes em camelCase com o X-Internal-Token e lê o id criado.
async def test_posts_camel_case_payload_with_internal_token() -> None:
    harness = RegistryHarness(ScriptedTransport.respond(201, CREATED))

    response = await harness.registry.register(SUBMISSION)

    (request,) = harness.requests
    assert request.url.path == "/internal/requisicoes"
    assert request.headers["X-Internal-Token"] == "token-de-teste-123"
    body = request.read().decode()
    assert '"idempotencyKey":"chave-1"' in body
    assert '"unitPrice":{"amount":"1999.99"' in body
    assert response.requisition.id == 7


# HTTP 422 do backend vira RequisitionRejectedError com o motivo devolvido.
async def test_422_becomes_rejection_with_backend_detail() -> None:
    harness = RegistryHarness(ScriptedTransport.respond(422, {"detail": "Estoque insuficiente."}))

    with pytest.raises(RequisitionRejectedError, match="Estoque insuficiente"):
        await harness.registry.register(SUBMISSION)


# HTTP 500 do backend vira registro indisponível, citando o status.
async def test_server_error_is_unavailable() -> None:
    harness = RegistryHarness(ScriptedTransport.respond(500, {"detail": "boom"}))

    with pytest.raises(RequisitionRegistryUnavailableError, match="500"):
        await harness.registry.register(SUBMISSION)


# Falha de conexão com o backend vira registro indisponível.
async def test_connection_failure_is_unavailable() -> None:
    harness = RegistryHarness(ScriptedTransport.refuse_connection())

    with pytest.raises(RequisitionRegistryUnavailableError, match="conectar"):
        await harness.registry.register(SUBMISSION)
