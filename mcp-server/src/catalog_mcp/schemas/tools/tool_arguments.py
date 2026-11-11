from typing import Annotated

from pydantic import Field

from catalog_mcp.schemas.product.product_category import ProductCategory
from catalog_mcp.schemas.tools.requisition_item_argument import RequisitionItemArgument

# Argumento "termo" de buscar_produtos.
SearchTerm = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        description="Termo de busca em inglês, ex.: 'laptop', 'phone', 'tablet'.",
    ),
]

# Argumento "categoria" de buscar_produtos, restrito às categorias da DummyJSON.
SearchCategory = Annotated[
    ProductCategory | None,
    Field(
        description=(
            "Categoria do catálogo onde buscar, ou null para buscar em todo o catálogo. "
            "Com categoria, o termo filtra por título ou marca dentro dela."
        ),
    ),
]

# Argumento "id" de detalhar_produto.
ProductId = Annotated[
    int,
    Field(ge=1, description="Id do produto, retornado por buscar_produtos."),
]

# Argumento de criar_requisicao: itens a gravar, de 1 a 20 por requisição.
RequisitionItems = Annotated[
    list[RequisitionItemArgument],
    Field(min_length=1, max_length=20, description="Itens a gravar: id do produto e quantidade."),
]

# Argumento de criar_requisicao: o que ficou de fora do pedido e por quê.
MissingItems = Annotated[
    list[str],
    Field(description="Itens do pedido que não serão atendidos e o motivo de cada um."),
]

# Argumento de criar_requisicao: mensagem final do agente para o usuário.
AgentMessage = Annotated[
    str,
    Field(min_length=1, max_length=1000, description="Resumo curto para o usuário, em português."),
]

# Argumento de criar_requisicao: teto de preço unitário citado pelo usuário, se houver.
MaxUnitPrice = Annotated[
    float | None,
    Field(ge=0, description="Orçamento máximo por unidade em USD citado no pedido, ou null."),
]

# Argumento de criar_requisicao: texto original do pedido, preenchido pelo sistema.
RequestText = Annotated[
    str,
    Field(min_length=1, max_length=1000, description="Preenchido pelo sistema."),
]

# Argumento de criar_requisicao: chave de idempotência, preenchida pelo sistema.
IdempotencyKey = Annotated[
    str,
    Field(min_length=1, max_length=100, description="Preenchido pelo sistema."),
]
