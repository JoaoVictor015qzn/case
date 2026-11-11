import logging
import time

from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response_input_param import FunctionCallOutput
from pydantic import JsonValue, TypeAdapter, ValidationError

from app.domain.ports.catalog_tools_gateway import CatalogToolsGateway
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.requisition_draft import RequisitionDraft
from app.schemas.agent.tool_call_trace import ToolCallTrace
from app.schemas.product.product_snapshot import ProductSnapshot

logger = logging.getLogger(__name__)


class ToolCallExecutor:
    """Executa as chamadas pedidas pelo modelo e acumula o que foi observado nesta execução."""

    ARGUMENTS = TypeAdapter(dict[str, JsonValue])
    INVALID_ARGUMENTS = "Argumentos inválidos para {name}: envie um objeto JSON com os parâmetros."

    def __init__(self, gateway: CatalogToolsGateway, mapper: ProductSnapshotMapper) -> None:
        self._gateway = gateway
        self._mapper = mapper
        self._traces: list[ToolCallTrace] = []
        self._observed: dict[int, ProductSnapshot] = {}

    async def execute(self, call: ResponseFunctionToolCall) -> FunctionCallOutput:
        arguments = self._parse_arguments(call.arguments)
        if arguments is None:
            self._record(call.name, {}, is_error=True, duration_ms=0)
            return self._output(call.call_id, self.INVALID_ARGUMENTS.format(name=call.name))

        started = time.perf_counter()
        result = await self._gateway.call_tool(call.name, arguments)
        duration_ms = round((time.perf_counter() - started) * 1000)
        self._record(call.name, arguments, is_error=result.is_error, duration_ms=duration_ms)
        for snapshot in self._mapper.from_tool_result(result):
            self._observed[snapshot.product_id] = snapshot
        return self._output(call.call_id, result.model_output())

    def finish(self, draft: RequisitionDraft) -> AgentRun:
        return AgentRun(
            draft=draft, observed_products=dict(self._observed), tool_calls=tuple(self._traces)
        )

    def _parse_arguments(self, raw: str) -> dict[str, JsonValue] | None:
        try:
            return self.ARGUMENTS.validate_json(raw)
        except ValidationError:
            return None

    def _record(
        self, name: str, arguments: dict[str, JsonValue], is_error: bool, duration_ms: int
    ) -> None:
        logger.info("tool_call name=%s is_error=%s duration_ms=%d", name, is_error, duration_ms)
        self._traces.append(
            ToolCallTrace(
                name=name, arguments=arguments, is_error=is_error, duration_ms=duration_ms
            )
        )

    @staticmethod
    def _output(call_id: str, output: str) -> FunctionCallOutput:
        return FunctionCallOutput(type="function_call_output", call_id=call_id, output=output)
