from app.domain.errors.domain_error import DomainError


class LLMConfigurationError(DomainError):
    user_message = (
        "O acesso ao modelo de linguagem foi recusado. "
        "Verifique a OPENROUTER_API_KEY e os créditos da conta."
    )
