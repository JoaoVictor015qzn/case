from secrets import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.interfaces.http.dependencies.settings_provider import SettingsDep


class InternalTokenGuard:
    """Protege as rotas que só o servidor MCP deve chamar (a porta 8000 é exposta no host)."""

    HEADER = "X-Internal-Token"
    DETAIL = "Token interno ausente ou inválido."

    # Dependência FastAPI: responde 401 se o header estiver ausente ou não bater com o token.
    @classmethod
    def verify(
        cls,
        settings: SettingsDep,
        token: Annotated[str | None, Header(alias=HEADER)] = None,
    ) -> None:
        # Comparação em tempo constante para não vazar o token por timing.
        expected = settings.internal_api_token.get_secret_value()
        if token is None or not compare_digest(token.encode(), expected.encode()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=cls.DETAIL)
