from app.domain.errors.domain_error import DomainError


# Erro quando a saída do agente não segue o schema estruturado esperado (HTTP 502)
class AgentOutputError(DomainError):
    user_message = "O agente devolveu uma resposta em formato inválido. Tente novamente."
