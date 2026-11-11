import re
import uuid
from typing import ClassVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.interfaces.http.middleware.correlation_id import CorrelationId


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Reaproveita o X-Request-ID do chat (ou gera um) e o devolve na resposta."""

    # Formato aceito para o id recebido; fora dele um novo id é gerado (evita injeção no log).
    VALID_ID: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

    # Define o correlation id do request, processa e o devolve no header da resposta.
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(CorrelationId.HEADER, "")
        correlation_id = incoming if self.VALID_ID.match(incoming) else uuid.uuid4().hex
        CorrelationId.set(correlation_id)
        response = await call_next(request)
        response.headers[CorrelationId.HEADER] = correlation_id
        return response
