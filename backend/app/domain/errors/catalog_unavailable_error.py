from app.domain.errors.domain_error import DomainError


class CatalogUnavailableError(DomainError):
    user_message = (
        "O catálogo de produtos está indisponível ou demorou demais para responder. "
        "Tente novamente em instantes."
    )
