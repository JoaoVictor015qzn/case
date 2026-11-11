import logging

from pydantic import JsonValue, ValidationError

from app.schemas.product.product_snapshot import ProductSnapshot
from app.schemas.tools.catalog_product_payload import CatalogProductPayload
from app.schemas.tools.tool_result import ToolResult

logger = logging.getLogger(__name__)


class ProductSnapshotMapper:
    """Extrai os produtos observados do resultado de buscar_produtos ou detalhar_produto."""

    # Chave da lista de produtos no resultado de buscar_produtos.
    PRODUCTS_KEY = "products"

    # Converte o resultado da ferramenta em snapshots; erro ou conteúdo vazio vira lista vazia.
    def from_tool_result(self, result: ToolResult) -> list[ProductSnapshot]:
        content = result.structured_content
        if result.is_error or content is None:
            return []
        # Busca traz uma lista em "products"; detalhar traz o produto direto no conteúdo.
        listed = content.get(self.PRODUCTS_KEY)
        payloads: list[JsonValue] = listed if isinstance(listed, list) else [content]
        snapshots = [self._parse(payload) for payload in payloads]
        return [snapshot for snapshot in snapshots if snapshot is not None]

    # Valida um produto do payload; se inválido, loga e o descarta.
    @staticmethod
    def _parse(payload: JsonValue) -> ProductSnapshot | None:
        try:
            return CatalogProductPayload.model_validate(payload).to_snapshot()
        except ValidationError as error:
            logger.warning("tool_payload_ignored errors=%d", error.error_count())
            return None
