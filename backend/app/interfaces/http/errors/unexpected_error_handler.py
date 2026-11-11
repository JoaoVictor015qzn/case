import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.api.error_response import ErrorResponse

logger = logging.getLogger(__name__)


class UnexpectedErrorHandler:
    """Erro não previsto: o stack vai para o log, o cliente recebe só uma mensagem clara."""

    DETAIL = "Erro inesperado ao processar o pedido. Tente novamente."

    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(Exception, self.handle)

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected_error path=%s", request.url.path, exc_info=exc)
        body = ErrorResponse(detail=self.DETAIL)
        return JSONResponse(status_code=500, content=body.model_dump(mode="json"))
