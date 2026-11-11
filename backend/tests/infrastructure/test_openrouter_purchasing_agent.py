import httpx2
import pytest

from app.domain.errors.agent_iteration_limit_error import AgentIterationLimitError
from app.domain.errors.agent_output_error import AgentOutputError
from app.domain.errors.llm_configuration_error import LLMConfigurationError
from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from app.infrastructure.llm.openai_error_translator import OpenAIErrorTranslator
from app.infrastructure.llm.openrouter_purchasing_agent import OpenRouterPurchasingAgent
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.schemas.agent.draft_item import DraftItem
from app.schemas.agent.draft_status import DraftStatus
from app.schemas.agent.requisition_draft import RequisitionDraft
from tests.fakes.catalog_tool_results import CatalogToolResults
from tests.fakes.fake_catalog_tools_gateway import FakeCatalogToolsGateway
from tests.fakes.sample_snapshots import SampleSnapshots
from tests.fakes.scripted_openrouter import ScriptedOpenRouter

pytestmark = pytest.mark.anyio

DRAFT = RequisitionDraft(
    status=DraftStatus.COMPLETE,
    max_unit_price=None,
    items=[DraftItem(product_id=78, quantity=2, reason="laptop pedido")],
    missing=[],
    message="Requisição montada.",
)


class AgentHarness:
    def __init__(self, openrouter: ScriptedOpenRouter, max_iterations: int = 4) -> None:
        self.gateway = FakeCatalogToolsGateway(
            {"buscar_produtos": CatalogToolResults.search(SampleSnapshots.MACBOOK)}
        )
        self.agent = OpenRouterPurchasingAgent(
            client=openrouter.client(),
            gateway=self.gateway,
            converter=McpToolSchemaConverter(),
            snapshot_mapper=ProductSnapshotMapper(),
            error_translator=OpenAIErrorTranslator(),
            model="openai/gpt-4.1-mini",
            max_iterations=max_iterations,
        )


async def test_runs_the_tools_the_model_asks_for_and_returns_what_was_observed() -> None:
    openrouter = ScriptedOpenRouter(
        ScriptedOpenRouter.function_call("buscar_produtos", {"termo": "laptop"}),
        ScriptedOpenRouter.final_draft(DRAFT),
    )
    harness = AgentHarness(openrouter)

    run = await harness.agent.run("2 notebooks")

    assert harness.gateway.calls == [("buscar_produtos", {"termo": "laptop"})]
    assert run.draft == DRAFT
    assert set(run.observed_products) == {78}
    assert [(call.name, call.is_error) for call in run.tool_calls] == [("buscar_produtos", False)]
    assert harness.gateway.closed is True


async def test_every_request_sends_tools_strict_schema_and_provider_preferences() -> None:
    openrouter = ScriptedOpenRouter(
        ScriptedOpenRouter.function_call("buscar_produtos", {"termo": "laptop"}),
        ScriptedOpenRouter.final_draft(DRAFT),
    )

    await AgentHarness(openrouter).agent.run("2 notebooks")

    for body in openrouter.requests:
        assert [tool["name"] for tool in body["tools"]] == ["buscar_produtos"]
        assert body["text"]["format"]["strict"] is True
        assert body["provider"] == {"require_parameters": True}


async def test_sends_the_tool_output_back_to_the_model() -> None:
    openrouter = ScriptedOpenRouter(
        ScriptedOpenRouter.function_call("buscar_produtos", {"termo": "laptop"}, "call_9"),
        ScriptedOpenRouter.final_draft(DRAFT),
    )

    await AgentHarness(openrouter).agent.run("2 notebooks")

    second_input = openrouter.requests[1]["input"]
    outputs = [item for item in second_input if item.get("type") == "function_call_output"]
    assert outputs[0]["call_id"] == "call_9"
    assert '"id": 78' in outputs[0]["output"]
    assert any(item.get("type") == "function_call" for item in second_input)


async def test_stops_at_the_iteration_limit() -> None:
    openrouter = ScriptedOpenRouter(
        ScriptedOpenRouter.function_call("buscar_produtos", {"termo": "laptop"}),
        ScriptedOpenRouter.function_call("buscar_produtos", {"termo": "laptop"}),
    )

    with pytest.raises(AgentIterationLimitError):
        await AgentHarness(openrouter, max_iterations=2).agent.run("2 notebooks")


async def test_invalid_final_answer_is_an_agent_output_error() -> None:
    openrouter = ScriptedOpenRouter(ScriptedOpenRouter.final_text("não é JSON"))

    with pytest.raises(AgentOutputError):
        await AgentHarness(openrouter).agent.run("2 notebooks")


async def test_invalid_api_key_is_a_configuration_error_and_closes_the_gateway() -> None:
    openrouter = ScriptedOpenRouter(
        httpx2.Response(401, json={"error": {"code": 401, "message": "User not found."}})
    )
    harness = AgentHarness(openrouter)

    with pytest.raises(LLMConfigurationError):
        await harness.agent.run("2 notebooks")

    assert harness.gateway.closed is True
