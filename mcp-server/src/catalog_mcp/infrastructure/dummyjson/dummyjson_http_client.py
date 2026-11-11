import logging
from typing import Any, Self

import anyio
import httpx

from catalog_mcp.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from catalog_mcp.schemas.settings.settings import Settings

logger = logging.getLogger(__name__)


class DummyJsonHttpClient:
    """Cliente HTTP da DummyJSON com timeout e retentativas com backoff exponencial.

    Só retenta falhas transitórias (timeout, conexão e 5xx); 4xx volta direto para quem chamou.
    """

    # Recebe o cliente httpx, o total de tentativas e o atraso base do backoff.
    def __init__(
        self, client: httpx.AsyncClient, max_attempts: int, retry_backoff_s: float
    ) -> None:
        self._client = client
        self._max_attempts = max_attempts
        self._retry_backoff_s = retry_backoff_s

    # Cria o cliente com URL base, timeout e política de retry vindos das Settings.
    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        client = httpx.AsyncClient(
            base_url=str(settings.dummyjson_base_url),
            timeout=httpx.Timeout(settings.dummyjson_timeout_s),
        )
        return cls(client, settings.dummyjson_max_attempts, settings.dummyjson_retry_backoff_s)

    # Faz GET na DummyJSON retentando falhas transitórias; esgotadas, levanta indisponível.
    async def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        failure = ""
        # Laço de tentativas: guarda o motivo da última falha para a mensagem final.
        for attempt in range(1, self._max_attempts + 1):
            # Erro de rede conta como falha transitória e segue para nova tentativa.
            try:
                response = await self._client.get(path, params=params)
            except httpx.TransportError as exc:
                failure = self._describe(exc)
            else:
                # Sucesso ou 4xx voltam direto; só 5xx é retentado.
                if not response.is_server_error:
                    return response
                failure = f"a DummyJSON respondeu com erro {response.status_code}"
            logger.warning(
                "dummyjson_attempt_failed path=%s attempt=%d reason=%s", path, attempt, failure
            )
            await self._wait_before_retry(attempt)
        raise CatalogUnavailableError(failure)

    # Fecha o cliente HTTP ao encerrar o servidor.
    async def aclose(self) -> None:
        await self._client.aclose()

    # Espera com backoff exponencial (base, 2x, 4x...), exceto após a última tentativa.
    async def _wait_before_retry(self, attempt: int) -> None:
        if attempt < self._max_attempts:
            await anyio.sleep(self._retry_backoff_s * 2 ** (attempt - 1))

    # Descreve a falha de rede em português, distinguindo timeout de falha de conexão.
    @staticmethod
    def _describe(error: httpx.TransportError) -> str:
        if isinstance(error, httpx.TimeoutException):
            return "a DummyJSON não respondeu a tempo"
        return "não foi possível conectar à DummyJSON"
