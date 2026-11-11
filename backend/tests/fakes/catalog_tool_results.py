from pydantic import JsonValue

from app.schemas.product.product_snapshot import ProductSnapshot
from app.schemas.tools.tool_definition import ToolDefinition
from app.schemas.tools.tool_result import ToolResult


class CatalogToolResults:
    """Resultados no mesmo formato que o servidor MCP do case devolve."""

    SEARCH_TOOL = ToolDefinition(
        name="buscar_produtos",
        description="Busca produtos no catálogo.",
        input_schema={
            "type": "object",
            "properties": {"termo": {"type": "string"}},
            "required": ["termo"],
        },
    )

    @classmethod
    def search(cls, *snapshots: ProductSnapshot) -> ToolResult:
        products: list[JsonValue] = [cls._payload(snapshot) for snapshot in snapshots]
        return ToolResult(
            is_error=False,
            text=f"{len(products)} produto(s)",
            structured_content={"products": products, "total": len(products)},
        )

    @classmethod
    def detail(cls, snapshot: ProductSnapshot) -> ToolResult:
        return ToolResult(
            is_error=False, text=snapshot.title, structured_content=cls._payload(snapshot)
        )

    @staticmethod
    def error(text: str) -> ToolResult:
        return ToolResult(is_error=True, text=text)

    @staticmethod
    def _payload(snapshot: ProductSnapshot) -> dict[str, JsonValue]:
        return {
            "id": snapshot.product_id,
            "title": snapshot.title,
            "category": snapshot.category,
            "price": snapshot.unit_price.model_dump(mode="json"),
            "stock": snapshot.stock,
            "minimum_order_quantity": snapshot.minimum_order_quantity,
            "availability_status": "In Stock",
        }
