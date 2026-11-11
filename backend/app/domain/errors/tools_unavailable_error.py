from app.domain.errors.domain_error import DomainError


# Erro quando não é possível conectar ao servidor MCP de ferramentas (HTTP 503)
class ToolsUnavailableError(DomainError):
    user_message = (
        "O serviço de ferramentas do agente (servidor MCP) está fora do ar. "
        "Tente novamente em instantes."
    )
