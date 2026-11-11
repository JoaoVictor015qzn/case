import logging
import time

from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response_input_param import FunctionCallOutput
from pydantic import JsonValue, TypeAdapter, ValidationError

from app.domain.ports.catalog_tools_gateway import CatalogToolsGateway
from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.schemas.agent.agent_request import AgentRequest
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.requisition_draft import RequisitionDraft
from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.product.product_snapshot import ProductSnapshot

logger = logging.getLogger(__name__)


class ToolCallExecutor:
    """Executa as chamadas pedidas pelo modelo e acumula o que foi observado nesta execução."""

    # Valida que os argumentos do modelo são um objeto JSON.
    ARGUMENTS = TypeAdapter(dict[str, JsonValue])
    # Mensagem devolvida ao modelo quando os argumentos não são JSON válido.
    INVALID_ARGUMENTS = "Argumentos inválidos para {name}: envie um objeto JSON com os parâmetros."

    # Guarda os colaboradores e o pedido; começa com trace e produtos observados vazios.
    def __init__(
        self,
        gateway: CatalogToolsGateway,
        mapper: ProductSnapshotMapper,
        policy: CreateRequisitionToolPolicy,
        request: AgentRequest,
    ) -> None:
        self._gateway = gateway
        self._mapper = mapper
        self._policy = policy
        self._request = request
        self._traces: list[ToolCallTrace] = []
        self._observed: dict[int, ProductSnapshot] = {}

    # Executa uma function_call do modelo e devolve o function_call_output correspondente.
    async def execute(self, call: ResponseFunctionToolCall) -> FunctionCallOutput:
        arguments = self._parse_arguments(call.arguments)
        # JSON inválido: registra erro no trace e pede ao modelo que reenvie os argumentos.
        if arguments is None:
            self._record(call.name, {}, is_error=True, duration_ms=0)
            return self._output(call.call_id, self.INVALID_ARGUMENTS.format(name=call.name))
        # criar_requisicao tem fluxo próprio (checagem de ids e argumentos do sistema).
        if self._policy.applies_to(call.name):
            return await self._create_requisition(call, arguments)

        # Ferramentas de leitura: chama o MCP, registra o trace e guarda os produtos vistos.
        started = time.perf_counter()
        result = await self._gateway.call_tool(call.name, arguments)
        self._record(call.name, arguments, is_error=result.is_error, started=started)
        for snapshot in self._mapper.from_tool_result(result):
            self._observed[snapshot.product_id] = snapshot
        return self._output(call.call_id, result.model_output())

    # Junta rascunho final, produtos observados e trace das chamadas no resultado da execução.
    def finish(self, draft: RequisitionDraft) -> AgentRun:
        return AgentRun(
            draft=draft, observed_products=dict(self._observed), tool_calls=tuple(self._traces)
        )

    # Trata criar_requisicao: recusa ids não observados e injeta os argumentos do sistema.
    async def _create_requisition(
        self, call: ResponseFunctionToolCall, arguments: dict[str, JsonValue]
    ) -> FunctionCallOutput:
        # Recusa sem chamar o MCP se algum id não apareceu nas buscas desta conversa.
        rejection = self._policy.rejection(arguments, self._observed.keys())
        if rejection is not None:
            self._record(call.name, arguments, is_error=True, duration_ms=0)
            return self._output(call.call_id, rejection)
        # Chama o MCP com request_text e idempotency_key injetados; o trace guarda os do modelo.
        started = time.perf_counter()
        result = await self._gateway.call_tool(
            call.name, self._policy.with_system_arguments(arguments, self._request)
        )
        self._record(call.name, arguments, is_error=result.is_error, started=started)
        return self._output(call.call_id, result.model_output())

    # Decodifica a string JSON de argumentos; devolve None se não for um objeto válido.
    def _parse_arguments(self, raw: str) -> dict[str, JsonValue] | None:
        try:
            return self.ARGUMENTS.validate_json(raw)
        except ValidationError:
            return None

    # Calcula a duração, loga a chamada e acrescenta um ToolCallTrace ao histórico.
    def _record(
        self,
        name: str,
        arguments: dict[str, JsonValue],
        is_error: bool,
        started: float | None = None,
        duration_ms: int = 0,
    ) -> None:
        if started is not None:
            duration_ms = round((time.perf_counter() - started) * 1000)
        logger.info("tool_call name=%s is_error=%s duration_ms=%d", name, is_error, duration_ms)
        self._traces.append(
            ToolCallTrace(
                name=name, arguments=arguments, is_error=is_error, duration_ms=duration_ms
            )
        )

    # Monta o item function_call_output que volta ao modelo com o resultado da ferramenta.
    @staticmethod
    def _output(call_id: str, output: str) -> FunctionCallOutput:
        return FunctionCallOutput(type="function_call_output", call_id=call_id, output=output)
