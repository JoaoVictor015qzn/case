from catalog_mcp.domain.errors.catalog_error import CatalogError


# Erro de domínio: o id pedido não existe no catálogo.
class ProductNotFoundError(CatalogError):
    # Guarda o id e monta a mensagem em português exibida ao modelo.
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Produto {product_id} não existe no catálogo.")
        self.product_id = product_id
