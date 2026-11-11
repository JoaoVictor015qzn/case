from app.domain.errors.domain_error import DomainError


class LLMTimeoutError(DomainError):
    user_message = "O modelo de linguagem demorou demais para responder. Tente novamente."
