from app.domain.errors.domain_error import DomainError


# Erro quando o LLM estoura o tempo limite de resposta (HTTP 504)
class LLMTimeoutError(DomainError):
    user_message = "O modelo de linguagem demorou demais para responder. Tente novamente."
