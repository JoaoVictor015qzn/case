from catalog_mcp.domain.errors.catalog_error import CatalogError


class RequisitionRegistryUnavailableError(CatalogError):
    """Não foi possível falar com o backend para gravar a requisição."""
