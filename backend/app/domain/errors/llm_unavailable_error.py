from app.domain.errors.domain_error import DomainError


# Erro quando o provedor do LLM falha ou está fora do ar (HTTP 502)
class LLMUnavailableError(DomainError):
    user_message = (
        "O modelo de linguagem está indisponível no momento. Tente novamente em instantes."
    )
