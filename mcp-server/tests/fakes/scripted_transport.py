from collections.abc import Callable

import httpx

from catalog_mcp.infrastructure.dummyjson.dummyjson_http_client import DummyJsonHttpClient

# Um passo do roteiro: recebe a requisição e devolve a resposta (ou levanta erro de rede).
Step = Callable[[httpx.Request], httpx.Response]


class ScriptedTransport:
    """httpx.MockTransport que responde cada requisição com o próximo passo do roteiro."""

    BASE_URL = "https://dummyjson.com"

    def __init__(self, *steps: Step) -> None:
        self._steps = list(steps)
        self.requests: list[httpx.Request] = []

    # Monta o DummyJsonHttpClient real sobre este transporte, sem espera entre tentativas.
    def http_client(self, max_attempts: int = 1) -> DummyJsonHttpClient:
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(self._handle), base_url=self.BASE_URL
        )
        return DummyJsonHttpClient(client, max_attempts=max_attempts, retry_backoff_s=0)

    # Registra a requisição e aplica o próximo passo; o último se repete quando acabam.
    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self._steps[min(len(self.requests), len(self._steps)) - 1]
        return step(request)

    # Passo que responde com o status e o corpo JSON informados.
    @staticmethod
    def respond(status: int, json: object | None = None) -> Step:
        return lambda _request: httpx.Response(status, json=json)

    # Passo que simula timeout de leitura.
    @staticmethod
    def time_out() -> Step:
        def step(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        return step

    # Passo que simula conexão recusada.
    @staticmethod
    def refuse_connection() -> Step:
        def step(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        return step
