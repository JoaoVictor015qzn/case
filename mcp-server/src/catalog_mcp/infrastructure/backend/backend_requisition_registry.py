import logging
from typing import Self

import httpx
from pydantic import SecretStr, ValidationError

from catalog_mcp.domain.errors.requisition_registry_unavailable_error import (
    RequisitionRegistryUnavailableError,
)
from catalog_mcp.domain.errors.requisition_rejected_error import RequisitionRejectedError
from catalog_mcp.domain.ports.requisition_registry import RequisitionRegistry
from catalog_mcp.schemas.requisition.registration_response import RegistrationResponse
from catalog_mcp.schemas.requisition.requisition_submission import RequisitionSubmission
from catalog_mcp.schemas.settings.settings import Settings

logger = logging.getLogger(__name__)


class BackendRequisitionRegistry(RequisitionRegistry):
    """Grava pelo endpoint interno do backend. Sem retry: a chave de idempotência já protege."""

    # Rota interna do backend e header que carrega o token compartilhado entre os serviços.
    PATH = "/internal/requisicoes"
    TOKEN_HEADER = "X-Internal-Token"

    # Recebe o cliente HTTP já configurado e o token interno (mantido como segredo).
    def __init__(self, client: httpx.AsyncClient, token: SecretStr) -> None:
        self._client = client
        self._token = token

    # Cria o cliente httpx com URL base e timeout do backend vindos das Settings.
    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        client = httpx.AsyncClient(
            base_url=str(settings.backend_url), timeout=httpx.Timeout(settings.backend_timeout_s)
        )
        return cls(client, settings.internal_api_token)

    # Envia a requisição ao backend e converte cada falha no erro de domínio adequado.
    async def register(self, submission: RequisitionSubmission) -> RegistrationResponse:
        # Falha de rede (timeout ou conexão) vira "registro indisponível".
        try:
            response = await self._client.post(
                self.PATH,
                json=submission.model_dump(mode="json"),
                headers={self.TOKEN_HEADER: self._token.get_secret_value()},
            )
        except httpx.TransportError as exc:
            raise RequisitionRegistryUnavailableError(self._describe(exc)) from exc
        # 422: o backend recusou a regra de negócio; o motivo é repassado ao modelo.
        if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
            raise RequisitionRejectedError(self._detail(response))
        # Qualquer outro erro HTTP é tratado como indisponibilidade do backend.
        if response.is_error:
            logger.warning("backend_register_failed status=%d", response.status_code)
            raise RequisitionRegistryUnavailableError(
                f"o backend respondeu com erro {response.status_code}"
            )
        # Valida o corpo de sucesso; formato inesperado também conta como indisponível.
        try:
            return RegistrationResponse.model_validate_json(response.content)
        except ValidationError as exc:
            raise RequisitionRegistryUnavailableError("resposta inválida do backend") from exc

    # Fecha o cliente HTTP ao encerrar o servidor.
    async def aclose(self) -> None:
        await self._client.aclose()

    # Extrai o campo "detail" da resposta de erro, com mensagem padrão se não houver.
    @staticmethod
    def _detail(response: httpx.Response) -> str:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None
        return detail if isinstance(detail, str) else "requisição recusada pelo backend"

    # Descreve a falha de rede em português, distinguindo timeout de falha de conexão.
    @staticmethod
    def _describe(error: httpx.TransportError) -> str:
        if isinstance(error, httpx.TimeoutException):
            return "o backend não respondeu a tempo"
        return "não foi possível conectar ao backend"
