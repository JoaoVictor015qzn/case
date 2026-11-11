from app.domain.errors.domain_error import DomainError


# Erro de gravação com chave de idempotência já usada por outra requisição (HTTP 409)
class DuplicateIdempotencyKeyError(DomainError):
    user_message = "Este pedido já foi registrado com a mesma chave de idempotência."

    # Guarda a chave repetida para o log
    def __init__(self, idempotency_key: str) -> None:
        super().__init__(f"idempotency_key={idempotency_key}")
        self.idempotency_key = idempotency_key
