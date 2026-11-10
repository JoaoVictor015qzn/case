from catalog_mcp.domain.errors.catalog_error import CatalogError


class ProductNotFoundError(CatalogError):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Produto {product_id} não existe no catálogo.")
        self.product_id = product_id
