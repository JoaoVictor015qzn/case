from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.api.error_response import ErrorResponse


class RequestValidationErrorHandler:
    """Corpo inválido vira `detail` em texto, no mesmo formato de todos os erros da API."""

    # Mensagem para o usuário final nas rotas públicas.
    DETAIL = "Pedido inválido: escreva o que você precisa comprar (de 3 a 1000 caracteres)."
    # Rotas internas (chamadas pelo MCP) recebem o detalhe de cada campo inválido.
    INTERNAL_PREFIX = "/internal/"
    INTERNAL_DETAIL = "Dados inválidos para criar a requisição: {errors}."

    # Registra o handler para os erros de validação do FastAPI.
    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(RequestValidationError, self.handle)

    # Responde 422 no formato ErrorResponse.
    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        body = ErrorResponse(detail=self._detail(request, exc))
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))

    # Escolhe a mensagem: genérica nas rotas públicas, lista de campos nas internas.
    def _detail(self, request: Request, exc: Exception) -> str:
        if not request.url.path.startswith(self.INTERNAL_PREFIX):
            return self.DETAIL
        # Resume cada erro como "campo: mensagem", sem o prefixo "body" do loc.
        errors = exc.errors() if isinstance(exc, RequestValidationError) else []
        summary = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'][1:])}: {error['msg']}"
            for error in errors
        )
        return self.INTERNAL_DETAIL.format(errors=summary or "corpo inválido")
