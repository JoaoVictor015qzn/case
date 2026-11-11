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
from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from app.infrastructure.llm.openai_error_translator import OpenAIErrorTranslator
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.infrastructure.llm.system_prompt import SystemPrompt
from app.infrastructure.llm.tool_call_executor import ToolCallExecutor
from app.schemas.agent.agent_request import AgentRequest
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.requisition_draft import RequisitionDraft

logger = logging.getLogger(__name__)


class OpenRouterPurchasingAgent(PurchasingAgent):
    """Loop de tool calling: o modelo decide quais ferramentas chamar e quando parar."""

    # Pede à OpenRouter só provedores que suportam todos os parâmetros enviados (tools, schema).
    PROVIDER_PREFERENCES: ClassVar[dict[str, object]] = {"provider": {"require_parameters": True}}

    # Recebe cliente OpenRouter, gateway MCP, colaboradores, modelo e limite de iterações.
    def __init__(
        self,
        client: AsyncOpenAI,
        gateway: CatalogToolsGateway,
        converter: McpToolSchemaConverter,
        snapshot_mapper: ProductSnapshotMapper,
        policy: CreateRequisitionToolPolicy,
        error_translator: OpenAIErrorTranslator,
        model: str,
        max_iterations: int,
    ) -> None:
        self._client = client
        self._gateway = gateway
        self._converter = converter
        self._snapshot_mapper = snapshot_mapper
        self._policy = policy
        self._error_translator = error_translator
        self._model = model
        self._max_iterations = max_iterations

    # Executa o agente: abre a sessão MCP, conversa com o modelo e devolve o rascunho e o trace.
    async def run(self, request: AgentRequest) -> AgentRun:
        async with self._gateway as gateway:
            # Lista as ferramentas do MCP e as converte para o formato function do modelo.
            tools = self._converter.convert(await gateway.list_tools())
            executor = ToolCallExecutor(gateway, self._snapshot_mapper, self._policy, request)
            conversation: list[ResponseInputItemParam] = [
                EasyInputMessageParam(role="user", content=request.request_text)
            ]
            output_error: AgentOutputError | None = None
            # Laço do agente: limitado a max_iterations turnos de chamada ao modelo.
            for _ in range(self._max_iterations):
                response = await self._ask_model(conversation, tools)
                # Reanexa response.output à conversa para o modelo ver o próprio turno.
                conversation.extend(self._as_input(response.output))
                calls = [i for i in response.output if isinstance(i, ResponseFunctionToolCall)]
                # Sem function_call o modelo terminou: valida a saída estruturada e encerra.
                if not calls:
                    try:
                        return executor.finish(self._parse_draft(response))
                    # Saída fora do schema volta ao modelo com os erros para ele corrigir.
                    except AgentOutputError as error:
                        output_error = error
                        conversation.append(self._correction_request(error))
                        continue
                output_error = None
                # Despacha cada function_call e anexa o resultado como function_call_output.
                for call in calls:
                    conversation.append(await executor.execute(call))
            # Se a última resposta veio fora do schema, esse é o erro que explica a falha.
            if output_error is not None:
                raise output_error
        raise AgentIterationLimitError(self._max_iterations)

    # Chama a Responses API com prompt, ferramentas e formato json_schema do rascunho.
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
        # Erros do SDK viram erros de domínio (timeout, configuração, indisponível).
        except openai.OpenAIError as error:
            raise self._error_translator.translate(error) from error
        # Resposta com status "failed" também é tratada como LLM indisponível.
        if response.status == "failed":
            raise LLMUnavailableError(response.error.message if response.error else "failed")
        self._log_usage(response)
        return response

    # Converte os itens de saída do modelo em itens de entrada da próxima chamada.
    @staticmethod
    def _as_input(output: list[ResponseOutputItem]) -> list[ResponseInputItemParam]:
        # Itens de saída voltam como entrada no próximo turno ("easy to forget this step").
        return [cast(ResponseInputItemParam, item.to_dict()) for item in output]

    # Valida o texto final contra o schema RequisitionDraft; falha vira AgentOutputError.
    @staticmethod
    def _parse_draft(response: Response) -> RequisitionDraft:
        if response.status != "completed":
            raise AgentOutputError(f"status={response.status}")
        try:
            return RequisitionDraft.model_validate_json(response.output_text)
        # Detalhe com campo e tipo de cada erro, sem os valores, para log e correção.
        except ValidationError as error:
            problems = "; ".join(
                f"{'.'.join(str(part) for part in item['loc']) or 'json'}: {item['type']}"
                for item in error.errors(include_url=False)
            )
            raise AgentOutputError(f"rascunho inválido: {problems}") from error

    # Mensagem que devolve ao modelo os erros da resposta final e pede só o JSON corrigido.
    @staticmethod
    def _correction_request(error: AgentOutputError) -> EasyInputMessageParam:
        return EasyInputMessageParam(
            role="user",
            content=(
                f"Sua resposta final não seguiu o formato exigido ({error.detail}). "
                "Responda de novo só com o JSON no formato pedido, sem repetir ferramentas "
                "que já deram certo."
            ),
        )

    # Registra no log o consumo de tokens da resposta, quando informado.
    @staticmethod
    def _log_usage(response: Response) -> None:
        if response.usage is not None:
            logger.info(
                "llm_response status=%s input_tokens=%d output_tokens=%d",
                response.status,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
