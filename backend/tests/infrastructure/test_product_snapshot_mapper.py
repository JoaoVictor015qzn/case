from app.infrastructure.llm.product_snapshot_mapper import ProductSnapshotMapper
from app.schemas.tools.tool_result import ToolResult
from tests.fakes.catalog_tool_results import CatalogToolResults
from tests.fakes.sample_snapshots import SampleSnapshots

mapper = ProductSnapshotMapper()


def test_reads_every_product_of_a_search() -> None:
    result = CatalogToolResults.search(SampleSnapshots.MACBOOK, SampleSnapshots.LENOVO)

    assert mapper.from_tool_result(result) == [SampleSnapshots.MACBOOK, SampleSnapshots.LENOVO]


def test_reads_a_product_detail() -> None:
    result = CatalogToolResults.detail(SampleSnapshots.IPHONE_6)

    assert mapper.from_tool_result(result) == [SampleSnapshots.IPHONE_6]


def test_ignores_malformed_products() -> None:
    result = ToolResult(
        is_error=False,
        text="",
        structured_content={"products": [{"id": 1, "title": "sem preço"}], "total": 1},
    )

    assert mapper.from_tool_result(result) == []


def test_error_results_observe_nothing() -> None:
    assert mapper.from_tool_result(CatalogToolResults.error("falhou")) == []
