from typing import Annotated

from pydantic import Field

SearchTerm = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        description="Termo de busca em inglês, ex.: 'laptop', 'phone', 'tablet'.",
    ),
]

ProductId = Annotated[
    int,
    Field(ge=1, description="Id do produto, retornado por buscar_produtos."),
]
