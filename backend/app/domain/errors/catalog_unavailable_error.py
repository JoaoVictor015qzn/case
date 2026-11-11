from app.domain.errors.domain_error import DomainError


# Erro quando o catálogo de produtos falha ou não responde a tempo (HTTP 503)
class CatalogUnavailableError(DomainError):
    user_message = (
        "O catálogo de produtos está indisponível ou demorou demais para responder. "
        "Tente novamente em instantes."
    )
