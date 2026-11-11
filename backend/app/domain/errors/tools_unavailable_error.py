from app.domain.errors.domain_error import DomainError


class ToolsUnavailableError(DomainError):
    user_message = (
        "O serviço de ferramentas do agente (servidor MCP) está fora do ar. "
        "Tente novamente em instantes."
    )
