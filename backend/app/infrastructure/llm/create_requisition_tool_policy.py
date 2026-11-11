from collections.abc import Collection

from pydantic import JsonValue

from app.schemas.agent.agent_request import AgentRequest


class CreateRequisitionToolPolicy:
    """Regras do backend para criar_requisicao, aplicadas antes de a chamada chegar ao MCP.

    - `request_text` e `idempotency_key` são do sistema: somem do schema que o modelo vê e são
      injetados na chamada, então o modelo não consegue trocar o pedido nem a chave.
    - Só aceita ids que apareceram em buscar_produtos/detalhar_produto nesta conversa.
    """

    TOOL_NAME = "criar_requisicao"
    # Argumentos preenchidos pelo backend e escondidos do modelo.
    SYSTEM_ARGUMENTS = ("request_text", "idempotency_key")
    # Mensagem devolvida ao modelo quando ele usa ids que não vieram das buscas.
    UNOBSERVED = (
        "Produto(s) {ids} não apareceram nas buscas desta conversa e nada foi gravado. "
        "Use só ids retornados por buscar_produtos ou detalhar_produto."
    )

    # Diz se a ferramenta chamada é a criar_requisicao.
    def applies_to(self, tool_name: str) -> bool:
        return tool_name == self.TOOL_NAME

    # Lista os argumentos a esconder do schema dessa ferramenta (vazio se não for a criação).
    def hidden_arguments(self, tool_name: str) -> tuple[str, ...]:
        return self.SYSTEM_ARGUMENTS if self.applies_to(tool_name) else ()

    # Devolve a mensagem de recusa se houver ids não observados; None se a chamada pode seguir.
    def rejection(
        self, arguments: dict[str, JsonValue], observed_ids: Collection[int]
    ) -> str | None:
        unobserved = [pid for pid in self._product_ids(arguments) if pid not in observed_ids]
        if not unobserved:
            return None
        return self.UNOBSERVED.format(ids=", ".join(str(pid) for pid in unobserved))

    # Injeta o texto original do pedido e a chave de idempotência nos argumentos do modelo.
    def with_system_arguments(
        self, arguments: dict[str, JsonValue], request: AgentRequest
    ) -> dict[str, JsonValue]:
        return {
            **arguments,
            "request_text": request.request_text,
            "idempotency_key": request.idempotency_key,
        }

    # Extrai os product_id inteiros da lista "items", ignorando entradas malformadas.
    @staticmethod
    def _product_ids(arguments: dict[str, JsonValue]) -> list[int]:
        items = arguments.get("items")
        if not isinstance(items, list):
            return []
        return [
            pid
            for item in items
            if isinstance(item, dict) and isinstance(pid := item.get("product_id"), int)
        ]
