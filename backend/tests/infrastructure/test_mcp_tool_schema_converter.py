from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from tests.fakes.catalog_tool_results import CatalogToolResults


def test_converts_to_responses_function_tool() -> None:
    (tool,) = McpToolSchemaConverter().convert([CatalogToolResults.SEARCH_TOOL])

    assert tool["type"] == "function"
    assert tool["name"] == "buscar_produtos"
    assert tool["parameters"] == CatalogToolResults.SEARCH_TOOL.input_schema
    assert tool["strict"] is False
