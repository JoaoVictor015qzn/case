from app.domain.errors.domain_error import DomainError


# Erro quando o loop do agente esgota o máximo de iterações sem resposta final (HTTP 502)
class AgentIterationLimitError(DomainError):
    user_message = (
        "O agente não chegou a uma resposta dentro do limite de etapas. Tente reformular o pedido."
    )

    # Guarda o limite de iterações atingido para o log
    def __init__(self, max_iterations: int) -> None:
        super().__init__(f"limite de {max_iterations} iterações atingido")
        self.max_iterations = max_iterations
