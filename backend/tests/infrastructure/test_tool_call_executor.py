import pytest
from openai.types.responses import ResponseFunctionToolCall

from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.infrastructure.llm.tool_call_executor import ToolCallExecutor
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.catalog_tool_results import CatalogToolResults
from tests.fakes.fake_catalog_tools_gateway import FakeCatalogToolsGateway
from tests.fakes.sample_snapshots import SampleSnapshots

pytestmark = pytest.mark.anyio


class CallFactory:
    @staticmethod
    def call(name: str, arguments: str) -> ResponseFunctionToolCall:
        return ResponseFunctionToolCall(
            type="function_call", call_id="call_1", name=name, arguments=arguments
        )


async def test_records_trace_and_observed_products() -> None:
    gateway = FakeCatalogToolsGateway(
        {"detalhar_produto": CatalogToolResults.detail(SampleSnapshots.IPHONE_6)}
    )
    executor = ToolCallExecutor(gateway, ProductSnapshotMapper())

    output = await executor.execute(CallFactory.call("detalhar_produto", '{"id": 122}'))
    run = executor.finish(AgentRunBuilder().build().draft)

    assert output["call_id"] == "call_1"
    assert run.observed_products[122] == SampleSnapshots.IPHONE_6
    assert run.tool_calls[0].arguments == {"id": 122}
    assert run.tool_calls[0].is_error is False


async def test_invalid_arguments_go_back_to_the_model_without_calling_the_tool() -> None:
    gateway = FakeCatalogToolsGateway()
    executor = ToolCallExecutor(gateway, ProductSnapshotMapper())

    output = await executor.execute(CallFactory.call("buscar_produtos", "{termo: laptop"))

    assert gateway.calls == []
    assert "Argumentos inválidos" in str(output["output"])
    assert executor.finish(AgentRunBuilder().build().draft).tool_calls[0].is_error is True


async def test_tool_error_is_reported_and_observes_nothing() -> None:
    gateway = FakeCatalogToolsGateway(
        {"buscar_produtos": CatalogToolResults.error("Catálogo indisponível.")}
    )
    executor = ToolCallExecutor(gateway, ProductSnapshotMapper())

    output = await executor.execute(CallFactory.call("buscar_produtos", '{"termo": "laptop"}'))
    run = executor.finish(AgentRunBuilder().build().draft)

    assert output["output"] == "Catálogo indisponível."
    assert run.observed_products == {}
    assert run.tool_calls[0].is_error is True
