import logging
from typing import ClassVar, cast

import openai
from openai import AsyncOpenAI
from openai.types.responses import (
    EasyInputMessageParam,
    FunctionToolParam,
    Response,
    ResponseFormatTextConfigParam,
    ResponseFunctionToolCall,
    ResponseInputItemParam,
    ResponseOutputItem,
)
from pydantic import ValidationError

from app.domain.errors.agent_iteration_limit_error import AgentIterationLimitError
from app.domain.errors.agent_output_error import AgentOutputError
from app.domain.errors.llm_unavailable_error import LLMUnavailableError
from app.domain.ports.catalog_tools_gateway import CatalogToolsGateway
from app.domain.ports.purchasing_agent import PurchasingAgent
from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from app.infrastructure.llm.openai_error_translator import OpenAIErrorTranslator
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.infrastructure.llm.system_prompt import SystemPrompt
from app.infrastructure.llm.tool_call_executor import ToolCallExecutor
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.requisition_draft import RequisitionDraft

logger = logging.getLogger(__name__)


class OpenRouterPurchasingAgent(PurchasingAgent):
    """Loop de tool calling: o modelo decide quais ferramentas chamar e quando parar."""

    PROVIDER_PREFERENCES: ClassVar[dict[str, object]] = {"provider": {"require_parameters": True}}

    def __init__(
        self,
        client: AsyncOpenAI,
        gateway: CatalogToolsGateway,
        converter: McpToolSchemaConverter,
        snapshot_mapper: ProductSnapshotMapper,
        error_translator: OpenAIErrorTranslator,
        model: str,
        max_iterations: int,
    ) -> None:
        self._client = client
        self._gateway = gateway
        self._converter = converter
        self._snapshot_mapper = snapshot_mapper
        self._error_translator = error_translator
        self._model = model
        self._max_iterations = max_iterations

    async def run(self, request_text: str) -> AgentRun:
        async with self._gateway as gateway:
            tools = self._converter.convert(await gateway.list_tools())
            executor = ToolCallExecutor(gateway, self._snapshot_mapper)
            conversation: list[ResponseInputItemParam] = [
                EasyInputMessageParam(role="user", content=request_text)
            ]
            for _ in range(self._max_iterations):
                response = await self._ask_model(conversation, tools)
                conversation.extend(self._as_input(response.output))
                calls = [i for i in response.output if isinstance(i, ResponseFunctionToolCall)]
                if not calls:
                    return executor.finish(self._parse_draft(response))
                for call in calls:
                    conversation.append(await executor.execute(call))
        raise AgentIterationLimitError(self._max_iterations)

    async def _ask_model(
        self, conversation: list[ResponseInputItemParam], tools: list[FunctionToolParam]
    ) -> Response:
        try:
            response = await self._client.responses.create(
                model=self._model,
                instructions=SystemPrompt.TEXT,
                tools=tools,
                input=conversation,
                text={
                    "format": cast(
                        ResponseFormatTextConfigParam, RequisitionDraft.response_format()
                    )
                },
                extra_body=self.PROVIDER_PREFERENCES,
            )
        except openai.OpenAIError as error:
            raise self._error_translator.translate(error) from error
        if response.status == "failed":
            raise LLMUnavailableError(response.error.message if response.error else "failed")
        self._log_usage(response)
        return response

    @staticmethod
    def _as_input(output: list[ResponseOutputItem]) -> list[ResponseInputItemParam]:
        # Itens de saída voltam como entrada no próximo turno ("easy to forget this step").
        return [cast(ResponseInputItemParam, item.to_dict()) for item in output]

    @staticmethod
    def _parse_draft(response: Response) -> RequisitionDraft:
        if response.status != "completed":
            raise AgentOutputError(f"status={response.status}")
        try:
            return RequisitionDraft.model_validate_json(response.output_text)
        except ValidationError as error:
            raise AgentOutputError(f"rascunho inválido: {error.error_count()} erro(s)") from error

    @staticmethod
    def _log_usage(response: Response) -> None:
        if response.usage is not None:
            logger.info(
                "llm_response status=%s input_tokens=%d output_tokens=%d",
                response.status,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
