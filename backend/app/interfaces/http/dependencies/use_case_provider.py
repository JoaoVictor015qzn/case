from typing import Annotated

from fastapi import Depends

from app.application.create_requisition_use_case import CreateRequisitionUseCase
from app.application.list_requisitions_use_case import ListRequisitionsUseCase
from app.application.register_requisition_use_case import RegisterRequisitionUseCase
from app.domain.services.grounding_validator import GroundingValidator
from app.domain.services.requisition_factory import RequisitionFactory
from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from app.infrastructure.llm.openai_error_translator import OpenAIErrorTranslator
from app.infrastructure.llm.openrouter_purchasing_agent import OpenRouterPurchasingAgent
from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.infrastructure.mcp.mcp_tools_gateway import McpToolsGateway
from app.infrastructure.persistence.mappers.requisition_table_mapper import (
    RequisitionTableMapper,
)
from app.infrastructure.persistence.sqlmodel_unit_of_work import SqlModelUnitOfWork
from app.interfaces.http.dependencies.application_resources import ApplicationResources
from app.interfaces.http.dependencies.resources_provider import ResourcesDep
from app.interfaces.http.dependencies.settings_provider import SettingsDep


class UseCaseProvider:
    """Monta os casos de uso por request. O agente e o gateway MCP não são compartilhados."""

    # Monta o caso de uso de criação com o agente OpenRouter e um gateway MCP novo.
    @staticmethod
    def create_requisition(
        resources: ResourcesDep, settings: SettingsDep
    ) -> CreateRequisitionUseCase:
        # A mesma política alimenta o conversor de schema e o agente.
        policy = CreateRequisitionToolPolicy()
        agent = OpenRouterPurchasingAgent(
            client=resources.llm_client,
            gateway=McpToolsGateway(str(settings.mcp_url), settings.mcp_timeout_s),
            converter=McpToolSchemaConverter(policy),
            snapshot_mapper=ProductSnapshotMapper(),
            policy=policy,
            error_translator=OpenAIErrorTranslator(),
            model=settings.openrouter_model,
            max_iterations=settings.agent_max_iterations,
        )
        return CreateRequisitionUseCase(agent, UseCaseProvider._unit_of_work(resources))

    # Monta o caso de uso que grava a requisição enviada pelo servidor MCP.
    @staticmethod
    def register_requisition(resources: ResourcesDep) -> RegisterRequisitionUseCase:
        return RegisterRequisitionUseCase(
            UseCaseProvider._unit_of_work(resources), GroundingValidator(), RequisitionFactory()
        )

    # Monta o caso de uso de listagem com o limite configurado.
    @staticmethod
    def list_requisitions(
        resources: ResourcesDep, settings: SettingsDep
    ) -> ListRequisitionsUseCase:
        return ListRequisitionsUseCase(
            UseCaseProvider._unit_of_work(resources), settings.requisitions_list_limit
        )

    # Cria um Unit of Work novo sobre o Database compartilhado.
    @staticmethod
    def _unit_of_work(resources: ApplicationResources) -> SqlModelUnitOfWork:
        return SqlModelUnitOfWork(resources.database, RequisitionTableMapper())


# Tipos anotados para injetar cada caso de uso nos routers via Depends.
CreateRequisitionDep = Annotated[
    CreateRequisitionUseCase, Depends(UseCaseProvider.create_requisition)
]
RegisterRequisitionDep = Annotated[
    RegisterRequisitionUseCase, Depends(UseCaseProvider.register_requisition)
]
ListRequisitionsDep = Annotated[ListRequisitionsUseCase, Depends(UseCaseProvider.list_requisitions)]
