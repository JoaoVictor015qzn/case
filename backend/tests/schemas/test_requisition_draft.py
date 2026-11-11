from decimal import Decimal

from app.schemas.agent.requisition_draft import RequisitionDraft
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.strict_schema_inspector import StrictSchemaInspector


# A saída estruturada é json_schema strict, sem campos extras e com todos obrigatórios.
def test_response_format_is_strict_json_schema() -> None:
    response_format = RequisitionDraft.response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["strict"] is True
    schema = response_format["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


# O schema aninhado de DraftItem também segue as regras do modo strict.
def test_nested_item_schema_is_strict() -> None:
    draft_item = RequisitionDraft.response_format()["schema"]["$defs"]["DraftItem"]

    assert draft_item["additionalProperties"] is False
    assert set(draft_item["required"]) == set(draft_item["properties"])


# Nenhum "$ref" tem chaves irmãs, construção que o modo strict recusa.
def test_no_ref_has_sibling_keywords() -> None:
    schema = RequisitionDraft.response_format()["schema"]

    assert StrictSchemaInspector.refs_with_siblings(schema) == []


# O teto em float do LLM vira Decimal limpo, sem ruído binário.
def test_budget_converts_float_without_binary_noise() -> None:
    draft = AgentRunBuilder().max_unit_price(1500.1).build().draft

    budget = draft.budget()

    assert budget is not None
    assert budget.max_unit_price.amount == Decimal("1500.10")


# Sem teto informado, o rascunho não tem orçamento.
def test_budget_is_none_without_limit() -> None:
    assert AgentRunBuilder().build().draft.budget() is None
