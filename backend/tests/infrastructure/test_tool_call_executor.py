import json

import pytest
from openai.types.responses import ResponseFunctionToolCall

from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.infrastructure.llm.tool_call_executor import ToolCallExecutor
from app.schemas.agent.agent_request import AgentRequest
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.catalog_tool_results import CatalogToolResults
from tests.fakes.fake_catalog_tools_gateway import FakeCatalogToolsGateway
from tests.fakes.sample_snapshots import SampleSnapshots

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio

# Pedido cujos texto e chave o executor injeta em criar_requisicao.
REQUEST = AgentRequest(request_text="2 macbooks", idempotency_key="chave-1")
# Argumentos que o modelo manda para criar_requisicao (sem os campos do sistema).
CREATE_ARGUMENTS = {
    "items": [{"product_id": 78, "quantity": 2}],
    "missing": [],
    "message": "ok",
    "max_unit_price": None,
}


# Cria tool calls da Responses API e o executor sobre o gateway falso.
class ExecutorFactory:
    # Tool call com argumentos em texto, como o modelo envia (pode ser JSON inválido).
    @staticmethod
    def call(name: str, arguments: str) -> ResponseFunctionToolCall:
        return ResponseFunctionToolCall(
            type="function_call", call_id="call_1", name=name, arguments=arguments
        )

    # Executor real com mapper e política de criar_requisicao para o REQUEST.
    @staticmethod
    def executor(gateway: FakeCatalogToolsGateway) -> ToolCallExecutor:
        return ToolCallExecutor(
            gateway, ProductSnapshotMapper(), CreateRequisitionToolPolicy(), REQUEST
        )


# Executar uma tool registra o rastro e os produtos vistos no resultado.
async def test_records_trace_and_observed_products() -> None:
    gateway = FakeCatalogToolsGateway(
        {"detalhar_produto": CatalogToolResults.detail(SampleSnapshots.IPHONE_6)}
    )
    executor = ExecutorFactory.executor(gateway)

    output = await executor.execute(ExecutorFactory.call("detalhar_produto", '{"id": 122}'))
    run = executor.finish(AgentRunBuilder().build().draft)

    assert output["call_id"] == "call_1"
    assert run.observed_products[122] == SampleSnapshots.IPHONE_6
    assert run.tool_calls[0].arguments == {"id": 122}
    assert run.tool_calls[0].is_error is False


# Argumentos com JSON inválido voltam como erro ao modelo e a tool não é chamada.
async def test_invalid_arguments_go_back_to_the_model_without_calling_the_tool() -> None:
    gateway = FakeCatalogToolsGateway()
    executor = ExecutorFactory.executor(gateway)

    output = await executor.execute(ExecutorFactory.call("buscar_produtos", "{termo: laptop"))

    assert gateway.calls == []
    assert "Argumentos inválidos" in str(output["output"])
    assert executor.finish(AgentRunBuilder().build().draft).tool_calls[0].is_error is True


# Erro da tool é repassado ao modelo e não conta nenhum produto como observado.
async def test_tool_error_is_reported_and_observes_nothing() -> None:
    gateway = FakeCatalogToolsGateway(
        {"buscar_produtos": CatalogToolResults.error("Catálogo indisponível.")}
    )
    executor = ExecutorFactory.executor(gateway)

    output = await executor.execute(ExecutorFactory.call("buscar_produtos", '{"termo": "laptop"}'))
    run = executor.finish(AgentRunBuilder().build().draft)

    assert output["output"] == "Catálogo indisponível."
    assert run.observed_products == {}
    assert run.tool_calls[0].is_error is True


# criar_requisicao com id não observado é barrada antes do MCP e nada é gravado.
async def test_criar_requisicao_with_unsearched_product_never_reaches_the_mcp() -> None:
    gateway = FakeCatalogToolsGateway({"criar_requisicao": CatalogToolResults.created(1)})
    executor = ExecutorFactory.executor(gateway)

    output = await executor.execute(
        ExecutorFactory.call("criar_requisicao", json.dumps(CREATE_ARGUMENTS))
    )

    assert gateway.calls == []
    assert "78" in str(output["output"])
    assert "nada foi gravado" in str(output["output"])


# O sistema sobrescreve texto e chave vindos do modelo e os omite do rastro.
async def test_criar_requisicao_receives_the_request_text_and_key_from_the_system() -> None:
    gateway = FakeCatalogToolsGateway(
        {
            "buscar_produtos": CatalogToolResults.search(SampleSnapshots.MACBOOK),
            "criar_requisicao": CatalogToolResults.created(1),
        }
    )
    executor = ExecutorFactory.executor(gateway)
    tampered = {**CREATE_ARGUMENTS, "idempotency_key": "chave-do-modelo"}

    await executor.execute(ExecutorFactory.call("buscar_produtos", '{"termo": "laptop"}'))
    output = await executor.execute(ExecutorFactory.call("criar_requisicao", json.dumps(tampered)))

    name, arguments = gateway.calls[1]
    assert name == "criar_requisicao"
    assert arguments["idempotency_key"] == "chave-1"
    assert arguments["request_text"] == "2 macbooks"
    assert '"requisition_id": 1' in str(output["output"])
    trace = executor.finish(AgentRunBuilder().build().draft).tool_calls[1]
    assert "request_text" not in trace.arguments
