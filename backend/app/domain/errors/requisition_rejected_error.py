from app.domain.errors.domain_error import DomainError


class RequisitionRejectedError(DomainError):
    """criar_requisicao pediu algo que o catálogo não permite. O texto volta para o modelo corrigir."""

    user_message = "A requisição proposta pelo agente não passou na verificação do catálogo."

    # Junta os motivos de recusa no detalhe e mantém a lista original
    def __init__(self, rejections: tuple[str, ...]) -> None:
        super().__init__(" ".join(rejections))
        self.rejections = rejections
