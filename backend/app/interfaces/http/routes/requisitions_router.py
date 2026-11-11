from typing import Annotated, Any, ClassVar

from fastapi import APIRouter, Header, Response, status

from app.interfaces.http.dependencies.use_case_provider import (
    CreateRequisitionDep,
    ListRequisitionsDep,
)
from app.schemas.api.create_requisition_request import CreateRequisitionRequest
from app.schemas.api.error_response import ErrorResponse
from app.schemas.api.requisition_created_response import RequisitionCreatedResponse
from app.schemas.api.requisition_public import RequisitionPublic

# Header opcional Idempotency-Key, validado e documentado no OpenAPI.
IdempotencyKeyHeader = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        max_length=100,
        description="Reenviar com a mesma chave devolve a requisição já criada.",
    ),
]


# Router público de requisições: POST e GET /requisicoes.
class RequisitionsRouter:
    # Respostas de erro documentadas no OpenAPI do POST.
    ERROR_RESPONSES: ClassVar[dict[int | str, dict[str, Any]]] = {
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Nada do pedido existe no catálogo (com `missing`) ou corpo inválido.",
        },
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse, "description": "Falha no LLM."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Servidor MCP ou catálogo indisponível.",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": ErrorResponse,
            "description": "O LLM demorou demais.",
        },
    }

    # Registra as rotas de criação e listagem no APIRouter.
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/requisicoes", tags=["requisicoes"])
        self.router.add_api_route(
            "",
            self.create,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            responses=self.ERROR_RESPONSES,
            summary="Cria uma requisição de compra a partir de um pedido em texto",
        )
        self.router.add_api_route(
            "", self.list_recent, methods=["GET"], summary="Lista as requisições mais recentes"
        )

    # Roda o agente sobre o pedido: 201 se criou, 200 se a Idempotency-Key já existia.
    async def create(
        self,
        body: CreateRequisitionRequest,
        use_case: CreateRequisitionDep,
        response: Response,
        idempotency_key: IdempotencyKeyHeader = None,
    ) -> RequisitionCreatedResponse:
        created = await use_case.execute(body.request_text, idempotency_key)
        if created.replayed:
            response.status_code = status.HTTP_200_OK
        return RequisitionCreatedResponse.from_domain(created)

    # Lista as requisições mais recentes no formato público.
    def list_recent(self, use_case: ListRequisitionsDep) -> list[RequisitionPublic]:
        return [RequisitionPublic.from_domain(requisition) for requisition in use_case.execute()]
