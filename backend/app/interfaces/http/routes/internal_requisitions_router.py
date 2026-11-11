from fastapi import APIRouter, Depends, Response, status

from app.interfaces.http.dependencies.internal_token_guard import InternalTokenGuard
from app.interfaces.http.dependencies.use_case_provider import RegisterRequisitionDep
from app.schemas.api.register_requisition_request import RegisterRequisitionRequest
from app.schemas.api.requisition_created_response import RequisitionCreatedResponse


class InternalRequisitionsRouter:
    """Rota chamada só pelo servidor MCP quando o agente usa criar_requisicao."""

    # Registra POST /internal/requisicoes, fora do OpenAPI e protegido pelo token interno.
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/internal/requisicoes",
            tags=["internal"],
            include_in_schema=False,
            dependencies=[Depends(InternalTokenGuard.verify)],
        )
        self.router.add_api_route(
            "", self.register, methods=["POST"], status_code=status.HTTP_201_CREATED
        )

    # Grava a requisição enviada pelo MCP: 201 se nova, 200 se a chave já existia.
    async def register(
        self,
        body: RegisterRequisitionRequest,
        use_case: RegisterRequisitionDep,
        response: Response,
    ) -> RequisitionCreatedResponse:
        created = await use_case.execute(body.to_registration())
        # Reenvio com a mesma idempotency_key devolve a existente com 200.
        if created.replayed:
            response.status_code = status.HTTP_200_OK
        return RequisitionCreatedResponse.from_domain(created)
