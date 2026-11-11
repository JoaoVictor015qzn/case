from typing import ClassVar


class DomainError(Exception):
    """Base dos erros do contexto Compras.

    `user_message` é o texto em pt-BR que chega ao chat; `detail` é o contexto técnico para o log.
    """

    user_message: ClassVar[str] = "Não foi possível concluir o pedido. Tente novamente."

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.user_message)
        self.detail = detail
