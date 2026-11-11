from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from pydantic import JsonValue

from app.schemas.tools.tool_definition import ToolDefinition
from app.schemas.tools.tool_result import ToolResult


class CatalogToolsGateway(ABC):
    """Conexão com as ferramentas do catálogo durante uma execução do agente.

    Falha de conexão vira ToolsUnavailableError. Erro de uma ferramenta não é exceção: volta
    como ToolResult(is_error=True) para o modelo decidir o próximo passo.
    """

    # Abre a conexão com o servidor de ferramentas
    @abstractmethod
    async def __aenter__(self) -> Self: ...

    # Fecha a conexão com o servidor de ferramentas
    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    # Lista as ferramentas disponíveis para oferecer ao modelo
    @abstractmethod
    async def list_tools(self) -> list[ToolDefinition]: ...

    # Executa uma ferramenta pelo nome com os argumentos escolhidos pelo modelo
    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> ToolResult: ...
