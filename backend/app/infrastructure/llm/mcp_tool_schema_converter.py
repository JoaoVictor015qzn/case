from openai.types.responses import FunctionToolParam

from app.schemas.tools.tool_definition import ToolDefinition


class McpToolSchemaConverter:
    """Ferramenta do catálogo -> formato `function` da Responses API."""

    def convert(self, tools: list[ToolDefinition]) -> list[FunctionToolParam]:
        return [self._to_function(tool) for tool in tools]

    @staticmethod
    def _to_function(tool: ToolDefinition) -> FunctionToolParam:
        parameters: dict[str, object] = dict(tool.input_schema)
        # strict exige additionalProperties=false em todo objeto; o schema vem do MCP como está.
        return FunctionToolParam(
            type="function",
            name=tool.name,
            description=tool.description,
            parameters=parameters,
            strict=False,
        )
