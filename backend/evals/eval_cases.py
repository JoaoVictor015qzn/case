from decimal import Decimal

from evals.eval_case import EvalCase


class EvalCases:
    """Os 5 pedidos do placar, conferidos contra o catálogo real da DummyJSON."""

    # Três pedidos que devem gerar requisição (201) e dois que nada atende (422).
    ALL = (
        EvalCase(
            name="3 laptops até US$ 2.000",
            request_text="Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada.",
            expect_status=201,
            category="laptops",
            quantity=3,
            max_unit_price=Decimal("2000"),
        ),
        EvalCase(
            name="notebook vira laptop",
            request_text="Preciso de 2 notebooks de até US$ 1.500 cada.",
            expect_status=201,
            category="laptops",
            quantity=2,
            max_unit_price=Decimal("1500"),
        ),
        EvalCase(
            name="2 smartphones até US$ 1.000",
            request_text="Quero 2 smartphones de até US$ 1.000 cada.",
            expect_status=201,
            category="smartphones",
            quantity=2,
            max_unit_price=Decimal("1000"),
        ),
        EvalCase(
            name="produto inexistente",
            request_text="Preciso de 5 Ferraris até US$ 10 cada.",
            expect_status=422,
        ),
        EvalCase(
            name="fora do orçamento",
            request_text="Quero 3 laptops por no máximo US$ 50 cada.",
            expect_status=422,
        ),
    )
