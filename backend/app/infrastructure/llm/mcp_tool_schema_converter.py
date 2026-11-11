from openai.types.responses import FunctionToolParam
from pydantic import JsonValue

from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.schemas.tools.tool_definition import ToolDefinition


class McpToolSchemaConverter:
    """Ferramenta do catálogo -> formato `function` da Responses API, sem argumentos do sistema."""

    # Recebe a política que define quais argumentos ficam ocultos do modelo.
    def __init__(self, policy: CreateRequisitionToolPolicy) -> None:
        self._policy = policy

    # Converte a lista de ferramentas do MCP em function tools da Responses API.
    def convert(self, tools: list[ToolDefinition]) -> list[FunctionToolParam]:
        return [self._to_function(tool) for tool in tools]

    # Monta a function tool de uma ferramenta, já sem os argumentos do sistema.
    def _to_function(self, tool: ToolDefinition) -> FunctionToolParam:
        parameters: dict[str, object] = self._without(
            tool.input_schema, self._policy.hidden_arguments(tool.name)
        )
        # strict exige additionalProperties=false em todo objeto; o schema vem do MCP como está.
        return FunctionToolParam(
            type="function",
            name=tool.name,
            description=tool.description,
            parameters=parameters,
            strict=False,
        )

    # Copia o JSON Schema removendo os campos ocultos de "properties" e de "required".
    @staticmethod
    def _without(schema: dict[str, JsonValue], hidden: tuple[str, ...]) -> dict[str, object]:
        parameters: dict[str, object] = dict(schema)
        if not hidden:
            return parameters
        properties = schema.get("properties")
        if isinstance(properties, dict):
            parameters["properties"] = {k: v for k, v in properties.items() if k not in hidden}
        required = schema.get("required")
        if isinstance(required, list):
            parameters["required"] = [name for name in required if name not in hidden]
        return parameters
