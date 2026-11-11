from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.schemas.agent.draft_status import DraftStatus
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.requisition_samples import RequisitionSamples
from tests.fakes.sample_snapshots import SampleSnapshots
from tests.interfaces.api_harness import ApiHarness

REQUEST = {"requestText": "2 macbooks"}


class AgentRuns:
    @staticmethod
    def two_macbooks() -> FakePurchasingAgent:
        run = (
            AgentRunBuilder()
            .observed(SampleSnapshots.MACBOOK)
            .item(78, 2)
            .tool_call("buscar_produtos")
            .build()
        )
        return FakePurchasingAgent(run)


def test_creates_requisition_and_returns_camel_case_body() -> None:
    harness = ApiHarness(AgentRuns.two_macbooks())

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 201
    body = response.json()
    assert body["requisition"]["id"] == 1
    assert body["requisition"]["total"] == {"amount": "3999.98", "currency": "USD"}
    assert body["requisition"]["items"][0]["unitPrice"] == {"amount": "1999.99", "currency": "USD"}
    assert body["toolCalls"][0]["name"] == "buscar_produtos"
    assert body["replayed"] is False


def test_replay_with_same_idempotency_key_returns_200_without_calling_agent_again() -> None:
    harness = ApiHarness(AgentRuns.two_macbooks())
    headers = {"Idempotency-Key": "abc-123"}

    first = harness.client.post("/requisicoes", json=REQUEST, headers=headers)
    second = harness.client.post("/requisicoes", json=REQUEST, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert second.json()["requisition"]["id"] == first.json()["requisition"]["id"]
    assert harness.agent.calls == 1


def test_nothing_found_returns_422_with_missing_and_tool_calls() -> None:
    run = (
        AgentRunBuilder()
        .status(DraftStatus.UNFULFILLABLE)
        .missing("Ferrari: não existe no catálogo.")
        .tool_call("buscar_produtos")
        .build()
    )
    harness = ApiHarness(FakePurchasingAgent(run))

    response = harness.client.post("/requisicoes", json={"requestText": "uma ferrari"})

    assert response.status_code == 422
    assert response.json()["missing"] == ["Ferrari: não existe no catálogo."]
    assert response.json()["toolCalls"][0]["name"] == "buscar_produtos"
    assert harness.unit_of_work.committed == []


def test_tools_unavailable_returns_503() -> None:
    harness = ApiHarness(FakePurchasingAgent(error=ToolsUnavailableError("conexão recusada")))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 503
    assert response.json()["detail"] == ToolsUnavailableError.user_message


def test_llm_timeout_returns_504() -> None:
    harness = ApiHarness(FakePurchasingAgent(error=LLMTimeoutError()))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 504


def test_invalid_body_returns_422_in_error_format() -> None:
    harness = ApiHarness()

    response = harness.client.post("/requisicoes", json={"requestText": "a"})

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Pedido inválido")
    assert harness.agent.calls == 0


def test_unexpected_error_returns_500_without_internal_details() -> None:
    harness = ApiHarness(FakePurchasingAgent(run=None))

    response = harness.client.post("/requisicoes", json=REQUEST)

    assert response.status_code == 500
    assert "AssertionError" not in response.text


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


def test_echoes_valid_request_id_and_replaces_invalid_one() -> None:
    harness = ApiHarness()

    echoed = harness.client.get("/health", headers={"X-Request-ID": "req-42"})
    replaced = harness.client.get("/health", headers={"X-Request-ID": "bad id with spaces"})

    assert echoed.json() == {"status": "ok"}
    assert echoed.headers["X-Request-ID"] == "req-42"
    assert replaced.headers["X-Request-ID"] != "bad id with spaces"
