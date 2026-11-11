from decimal import Decimal
from typing import Any

from evals.catalog_reference import CatalogReference
from evals.eval_case import EvalCase


class EvalChecker:
    """Aplica as regras de acerto à resposta de POST /requisicoes."""

    # Ferramenta que precisa aparecer no trace de toda requisição criada.
    SAVE_TOOL = "criar_requisicao"

    # Recebe a referência independente do catálogo usada para conferir os itens.
    def __init__(self, catalog: CatalogReference) -> None:
        self._catalog = catalog

    # Devolve os motivos de falha do caso; lista vazia significa acerto.
    def check(self, case: EvalCase, status_code: int, body: dict[str, Any]) -> list[str]:
        if status_code != case.expect_status:
            return [f"status {status_code}, esperado {case.expect_status}: {body.get('detail')}"]
        if status_code != 201:
            return []
        return self._check_requisition(case, body)

    # Confere a requisição criada: cada item, quantidade total, soma e uso de criar_requisicao.
    def _check_requisition(self, case: EvalCase, body: dict[str, Any]) -> list[str]:
        requisition = body["requisition"]
        items = requisition["items"]
        reasons = [self._check_item(case, item) for item in items]
        reasons = [reason for reason in reasons if reason]
        # Quantidade somada de todos os itens deve bater com a pedida.
        quantity = sum(item["quantity"] for item in items)
        if case.quantity is not None and quantity != case.quantity:
            reasons.append(f"quantidade total {quantity}, esperado {case.quantity}")
        # O total da requisição deve ser a soma exata dos subtotais.
        total = sum((Decimal(item["lineTotal"]["amount"]) for item in items), Decimal(0))
        if Decimal(requisition["total"]["amount"]) != total:
            reasons.append(f"total {requisition['total']['amount']} difere da soma {total}")
        if self.SAVE_TOOL not in (call["name"] for call in body["toolCalls"]):
            reasons.append(f"requisição salva sem chamada a {self.SAVE_TOOL}")
        return reasons

    # Confere o item na DummyJSON: existência, título, preço, categoria, orçamento, subtotal.
    def _check_item(self, case: EvalCase, item: dict[str, Any]) -> str | None:
        product = self._catalog.get(item["productId"])
        unit_price = Decimal(item["unitPrice"]["amount"])
        if product is None:
            return f"produto {item['productId']} não existe na DummyJSON"
        if product.title != item["title"] or product.price != unit_price:
            return f"{item['title']}: título ou preço diferente do catálogo"
        if case.category is not None and product.category != case.category:
            return f"{product.title}: categoria {product.category}, esperado {case.category}"
        if case.max_unit_price is not None and unit_price > case.max_unit_price:
            return f"{product.title}: {unit_price} acima do orçamento {case.max_unit_price}"
        if unit_price * item["quantity"] != Decimal(item["lineTotal"]["amount"]):
            return f"{product.title}: subtotal não bate com preço x quantidade"
        return None
