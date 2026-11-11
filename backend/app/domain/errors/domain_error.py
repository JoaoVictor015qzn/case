from typing import ClassVar


class DomainError(Exception):
    """Base dos erros do contexto Compras.

    `user_message` é o texto em pt-BR que chega ao chat; `detail` é o contexto técnico para o log.
    """

    # Mensagem genérica usada quando a subclasse não define a sua
    user_message: ClassVar[str] = "Não foi possível concluir o pedido. Tente novamente."

    # Guarda o detalhe técnico; sem detalhe, a exceção usa a mensagem ao usuário
    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.user_message)
        self.detail = detail
