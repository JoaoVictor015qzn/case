from app.domain.errors.domain_error import DomainError


class LLMUnavailableError(DomainError):
    user_message = (
        "O modelo de linguagem está indisponível no momento. Tente novamente em instantes."
    )
