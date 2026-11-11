from app.infrastructure.llm.create_requisition_tool_policy import CreateRequisitionToolPolicy
from app.infrastructure.llm.mcp_tool_schema_converter import McpToolSchemaConverter
from tests.fakes.catalog_tool_results import CatalogToolResults

converter = McpToolSchemaConverter(CreateRequisitionToolPolicy())


# A tool MCP vira function tool da Responses API com o mesmo schema, sem strict.
def test_converts_to_responses_function_tool() -> None:
    (tool,) = converter.convert([CatalogToolResults.SEARCH_TOOL])

    assert tool["type"] == "function"
    assert tool["name"] == "buscar_produtos"
    assert tool["parameters"] == CatalogToolResults.SEARCH_TOOL.input_schema
    assert tool["strict"] is False


# request_text e idempotency_key somem do schema que o modelo vê em criar_requisicao.
def test_hides_system_arguments_of_criar_requisicao_from_the_model() -> None:
    (tool,) = converter.convert([CatalogToolResults.CREATE_TOOL])

    parameters = tool["parameters"]
    assert isinstance(parameters, dict)
    properties = parameters["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"items", "missing", "message", "max_unit_price"}
    assert parameters["required"] == ["items", "missing", "message", "max_unit_price"]
