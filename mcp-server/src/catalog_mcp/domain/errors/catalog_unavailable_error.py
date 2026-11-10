from catalog_mcp.domain.errors.catalog_error import CatalogError


class CatalogUnavailableError(CatalogError):
    """O catálogo externo não respondeu, demorou demais ou devolveu algo inesperado."""
