from pydantic import JsonValue

from app.schemas.product.product_snapshot import ProductSnapshot
from app.schemas.tools.tool_definition import ToolDefinition
from app.schemas.tools.tool_result import ToolResult


class CatalogToolResults:
    """Resultados no mesmo formato que o servidor MCP do case devolve."""

    # Definição mínima de buscar_produtos como o gateway MCP a entrega ao agente.
    SEARCH_TOOL = ToolDefinition(
        name="buscar_produtos",
        description="Busca produtos no catálogo.",
        input_schema={
            "type": "object",
            "properties": {"termo": {"type": "string"}},
            "required": ["termo"],
        },
    )
    # Definição de criar_requisicao com todos os argumentos obrigatórios do servidor real.
    CREATE_TOOL = ToolDefinition(
        name="criar_requisicao",
        description="Grava a requisição.",
        input_schema={
            "type": "object",
            "properties": {
                "items": {"type": "array"},
                "missing": {"type": "array"},
                "message": {"type": "string"},
                "max_unit_price": {"type": ["number", "null"]},
                "request_text": {"type": "string"},
                "idempotency_key": {"type": "string"},
            },
            "required": [
                "items",
                "missing",
                "message",
                "max_unit_price",
                "request_text",
                "idempotency_key",
            ],
        },
    )

    # Resultado de criar_requisicao com sucesso, trazendo o número gravado.
    @staticmethod
    def created(requisition_id: int) -> ToolResult:
        return ToolResult(
            is_error=False,
            text=f"Requisição {requisition_id} gravada",
            structured_content={
                "requisition_id": requisition_id,
                "status": "complete",
                "total": {"amount": "3999.98", "currency": "USD"},
                "replayed": False,
            },
        )

    # Resultado de buscar_produtos com os produtos informados.
    @classmethod
    def search(cls, *snapshots: ProductSnapshot) -> ToolResult:
        products: list[JsonValue] = [cls._payload(snapshot) for snapshot in snapshots]
        return ToolResult(
            is_error=False,
            text=f"{len(products)} produto(s)",
            structured_content={"products": products, "total": len(products)},
        )

    # Resultado de detalhar_produto para um produto.
    @classmethod
    def detail(cls, snapshot: ProductSnapshot) -> ToolResult:
        return ToolResult(
            is_error=False, text=snapshot.title, structured_content=cls._payload(snapshot)
        )

    # Resultado de erro de tool com a mensagem informada.
    @staticmethod
    def error(text: str) -> ToolResult:
        return ToolResult(is_error=True, text=text)

    # Converte o snapshot no JSON de produto que o servidor MCP devolve.
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
