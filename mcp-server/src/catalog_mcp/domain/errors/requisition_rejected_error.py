from catalog_mcp.domain.errors.catalog_error import CatalogError


class RequisitionRejectedError(CatalogError):
    """O backend recusou a requisição (ex.: quantidade acima do estoque). Nada foi gravado."""
