from app.domain.errors.domain_error import DomainError


class AgentOutputError(DomainError):
    user_message = "O agente devolveu uma resposta em formato inválido. Tente novamente."
