from decimal import Decimal
from typing import Any

import httpx

from evals.catalog_reference import CatalogReference
from evals.eval_case import EvalCase
from evals.eval_checker import EvalChecker

# Caso de avaliação: 2 laptops com teto de 2000, esperando requisição criada (201).
CASE = EvalCase(
    name="laptops",
    request_text="2 laptops até 2000",
    expect_status=201,
    category="laptops",
    quantity=2,
    max_unit_price=Decimal("2000"),
)
# Produto como o catálogo de referência devolve em /products/78.
MACBOOK = {"id": 78, "title": "Apple MacBook Pro", "category": "laptops", "price": 1999.99}


# Monta o EvalChecker sobre catálogo simulado e respostas da API para conferir.
class CheckerHarness:
    # Checker com catálogo que só conhece o produto 78; os demais dão 404.
    @staticmethod
    def checker() -> EvalChecker:
        def handle(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/products/78":
                return httpx.Response(200, json=MACBOOK)
            return httpx.Response(404, json={"message": "not found"})

        client = httpx.Client(
            base_url="https://catalog.test", transport=httpx.MockTransport(handle)
        )
        return EvalChecker(CatalogReference(client))

    # Resposta de POST /requisicoes com um item; o padrão bate com o catálogo e o caso.
    @staticmethod
    def body(
        product_id: int = 78, unit_price: str = "1999.99", quantity: int = 2, total: str = "3999.98"
    ) -> dict[str, Any]:
        item = {
            "productId": product_id,
            "title": "Apple MacBook Pro",
            "unitPrice": {"amount": unit_price, "currency": "USD"},
            "quantity": quantity,
            "lineTotal": {"amount": total, "currency": "USD"},
        }
        return {
            "requisition": {"items": [item], "total": {"amount": total, "currency": "USD"}},
            "toolCalls": [{"name": "buscar_produtos"}, {"name": "criar_requisicao"}],
        }


# Requisição fiel ao catálogo e ao caso passa sem nenhum motivo de falha.
def test_grounded_requisition_passes() -> None:
    assert CheckerHarness.checker().check(CASE, 201, CheckerHarness.body()) == []


# Preço diferente do catálogo reprova o caso (indício de valor inventado).
def test_price_different_from_the_catalog_fails() -> None:
    body = CheckerHarness.body(unit_price="999.99", total="1999.98")

    reasons = CheckerHarness.checker().check(CASE, 201, body)

    assert reasons == ["Apple MacBook Pro: título ou preço diferente do catálogo"]


# Produto que não existe na DummyJSON reprova o caso.
def test_product_missing_from_the_catalog_fails() -> None:
    reasons = CheckerHarness.checker().check(CASE, 201, CheckerHarness.body(product_id=1))

    assert reasons == ["produto 1 não existe na DummyJSON"]


# Quantidade diferente da pedida ou status HTTP inesperado reprovam o caso.
def test_wrong_quantity_and_wrong_status_fail() -> None:
    checker = CheckerHarness.checker()

    assert checker.check(CASE, 201, CheckerHarness.body(quantity=1, total="1999.99")) == [
        "quantidade total 1, esperado 2"
    ]
    assert checker.check(CASE, 422, {"detail": "nada"}) == ["status 422, esperado 201: nada"]
