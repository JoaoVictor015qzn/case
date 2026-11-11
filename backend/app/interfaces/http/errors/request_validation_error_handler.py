from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.api.error_response import ErrorResponse


class RequestValidationErrorHandler:
    """Corpo inválido vira `detail` em texto, no mesmo formato de todos os erros da API."""

    DETAIL = "Pedido inválido: escreva o que você precisa comprar (de 3 a 1000 caracteres)."

    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(RequestValidationError, self.handle)

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        body = ErrorResponse(detail=self.DETAIL)
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
