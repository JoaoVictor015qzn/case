from tests.interfaces.api_harness import ApiHarness

PATH = "/internal/requisicoes"


# Corpos em camelCase como o servidor MCP envia ao endpoint interno.
class Payloads:
    # Pedido de MacBooks com quantidade e teto ajustáveis para provocar violações.
    @staticmethod
    def build(quantity: int = 2, max_unit_price: str | None = "2000") -> dict[str, object]:
        return {
            "requestText": "2 macbooks",
            "idempotencyKey": "chave-1",
            "items": [
                {
                    "productId": 78,
                    "title": "Apple MacBook Pro 14 Inch Space Grey",
                    "category": "laptops",
                    "unitPrice": {"amount": "1999.99", "currency": "USD"},
                    "stock": 24,
                    "minimumOrderQuantity": 1,
                    "quantity": quantity,
                }
            ],
            "maxUnitPrice": max_unit_price,
            "missing": [],
            "message": "Requisição montada.",
        }


# Registro válido com token responde 201 com o total e grava com a chave enviada.
def test_saves_and_returns_201_with_the_requisition() -> None:
    harness = ApiHarness()

    response = harness.client.post(PATH, json=Payloads.build(), headers=ApiHarness.INTERNAL_HEADERS)

    assert response.status_code == 201
    assert response.json()["requisition"]["total"] == {"amount": "3999.98", "currency": "USD"}
    assert harness.unit_of_work.committed[0].idempotency_key == "chave-1"


# Reenviar com a mesma chave responde 200 replayed e não grava de novo.
def test_same_key_returns_200_replayed() -> None:
    harness = ApiHarness()
    headers = ApiHarness.INTERNAL_HEADERS

    harness.client.post(PATH, json=Payloads.build(), headers=headers)
    second = harness.client.post(PATH, json=Payloads.build(), headers=headers)

    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert len(harness.unit_of_work.committed) == 1


# Violação de regra (estoque) responde 422 com o motivo para o modelo corrigir.
def test_rule_violation_returns_422_with_the_reason_for_the_model() -> None:
    harness = ApiHarness()

    response = harness.client.post(
        PATH, json=Payloads.build(quantity=25), headers=ApiHarness.INTERNAL_HEADERS
    )

    assert response.status_code == 422
    assert "Estoque insuficiente" in response.json()["detail"]
    assert harness.unit_of_work.committed == []


# Sem X-Internal-Token ou com token errado responde 401 e nada é gravado.
def test_requires_the_internal_token() -> None:
    harness = ApiHarness()

    missing = harness.client.post(PATH, json=Payloads.build())
    wrong = harness.client.post(PATH, json=Payloads.build(), headers={"X-Internal-Token": "x"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert harness.unit_of_work.committed == []


# A rota interna não aparece no OpenAPI público.
def test_internal_route_is_hidden_from_the_public_docs() -> None:
    schema = ApiHarness().client.get("/openapi.json").json()

    assert PATH not in schema["paths"]
