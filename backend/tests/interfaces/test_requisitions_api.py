from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.requisition_not_saved_error import RequisitionNotSavedError
from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.schemas.agent.draft_status import DraftStatus
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.requisition_samples import RequisitionSamples
from tests.interfaces.api_harness import ApiHarness

# Corpo de POST /requisicoes em camelCase, como o frontend envia.
REQUEST = {"requestText": "1 macbook e 2 lenovos"}
# Execução do agente que buscou e gravou via criar_requisicao, terminando parcial.
SAVED_RUN = (
    AgentRunBuilder()
    .status(DraftStatus.PARTIAL)
    .tool_call("buscar_produtos")
    .tool_call("criar_requisicao")
    .build()
)


# Responde 201 com a requisição gravada, faltantes e tools chamadas, em camelCase.
def test_returns_what_the_agent_saved_in_camel_case() -> None:
    harness = ApiHarness(SAVED_RUN, agent_saves=RequisitionSamples.two_laptops())

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 201
    body = response.json()
    assert body["requisition"]["id"] == 1
    assert body["requisition"]["total"] == {"amount": "4199.97", "currency": "USD"}
    assert body["requisition"]["items"][0]["unitPrice"] == {"amount": "1999.99", "currency": "USD"}
    assert [call["name"] for call in body["toolCalls"]] == ["buscar_produtos", "criar_requisicao"]
    assert body["missing"] == ["Mouse sem fio: não encontrado."]
    assert body["replayed"] is False


# Mesma Idempotency-Key responde 200 replayed com a mesma requisição e sem rodar o agente.
def test_replay_with_same_idempotency_key_returns_200_without_calling_agent_again() -> None:
    harness = ApiHarness(SAVED_RUN, agent_saves=RequisitionSamples.two_laptops())
    headers = {"Idempotency-Key": "abc-123"}

    first = harness.client.post("/requisicoes", json=REQUEST, headers=headers)
    second = harness.client.post("/requisicoes", json=REQUEST, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert second.json()["requisition"]["id"] == first.json()["requisition"]["id"]
    assert harness.agent.calls == 1


# Nada atendível responde 422 com faltantes e tools chamadas, sem gravar.
def test_nothing_found_returns_422_with_missing_and_tool_calls() -> None:
    run = (
        AgentRunBuilder()
        .status(DraftStatus.UNFULFILLABLE)
        .missing("Ferrari: não existe no catálogo.")
        .tool_call("buscar_produtos")
        .build()
    )
    harness = ApiHarness(run)

    response = harness.client.post("/requisicoes", json={"requestText": "uma ferrari"})

    assert response.status_code == 422
    assert response.json()["missing"] == ["Ferrari: não existe no catálogo."]
    assert response.json()["toolCalls"][0]["name"] == "buscar_produtos"
    assert harness.unit_of_work.committed == []


# Agente que diz ter concluído sem gravar resulta em 502 com mensagem amigável.
def test_agent_that_claims_success_without_saving_returns_502() -> None:
    harness = ApiHarness(AgentRunBuilder().status(DraftStatus.COMPLETE).build())

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 502
    assert response.json()["detail"] == RequisitionNotSavedError.user_message


# Servidor MCP indisponível resulta em 503 com mensagem amigável.
def test_tools_unavailable_returns_503() -> None:
    harness = ApiHarness(agent=FakePurchasingAgent(error=ToolsUnavailableError("recusada")))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 503
    assert response.json()["detail"] == ToolsUnavailableError.user_message


# Timeout do LLM resulta em 504.
def test_llm_timeout_returns_504() -> None:
    harness = ApiHarness(agent=FakePurchasingAgent(error=LLMTimeoutError()))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 504


# Corpo inválido (texto curto demais) responde 422 no formato de erro e não chama o agente.
def test_invalid_body_returns_422_in_error_format() -> None:
    harness = ApiHarness()

    response = harness.client.post("/requisicoes", json={"requestText": "a"})

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Pedido inválido")
    assert harness.agent.calls == 0


# Erro inesperado responde 500 sem vazar detalhes internos como o tipo da exceção.
def test_unexpected_error_returns_500_without_internal_details() -> None:
    harness = ApiHarness(agent=FakePurchasingAgent(run=None))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 500
    assert "AssertionError" not in response.text


# GET /requisicoes lista as mais recentes primeiro, com os faltantes.
def test_lists_recent_requisitions_newest_first() -> None:
    older = RequisitionSamples.two_laptops(minutes_after_start=0)
    newer = RequisitionSamples.two_laptops(minutes_after_start=5)
    saved = [
        older.with_identity(1, older.created_at),
        newer.with_identity(2, newer.created_at),
    ]
    harness = ApiHarness(saved=saved)

    response = harness.client.get("/requisicoes")

    assert response.status_code == 200
    assert [requisition["id"] for requisition in response.json()] == [2, 1]
    assert response.json()[0]["missing"] == ["Mouse sem fio: não encontrado."]


# X-Request-ID válido é ecoado na resposta; um inválido é substituído por outro gerado.
def test_echoes_valid_request_id_and_replaces_invalid_one() -> None:
    harness = ApiHarness()

    echoed = harness.client.get("/health", headers={"X-Request-ID": "req-42"})
    replaced = harness.client.get("/health", headers={"X-Request-ID": "bad id with spaces"})

    assert echoed.json() == {"status": "ok"}
    assert echoed.headers["X-Request-ID"] == "req-42"
    assert replaced.headers["X-Request-ID"] != "bad id with spaces"
