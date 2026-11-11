# Servidor MCP (contexto Catálogo)

Pasta `mcp-server/`. Expõe o catálogo da DummyJSON como tools MCP via **Streamable HTTP stateless** em `http://mcp-server:8000/mcp` (só na rede interna do compose), mais `GET /health`.

## Tools

### `buscar_produtos(termo, categoria=None)`

Busca produtos por palavra-chave.

| Argumento | Tipo | Regra |
|---|---|---|
| `termo` | texto, 1–100 caracteres | Obrigatório. Em inglês (o catálogo é em inglês) |
| `categoria` | uma das 24 categorias da DummyJSON, ou `null` | Opcional. O schema da tool lista os valores válidos |

- **Sem categoria**: `GET /products/search?q=<termo>` (até `SEARCH_LIMIT` resultados, padrão 10).
- **Com categoria**: `GET /products/category/<categoria>` (a categoria inteira, no máximo 30 produtos) filtrada pelas palavras do termo no título ou na marca. Se nenhum produto tiver o termo, devolve a categoria inteira, para o modelo ver o que existe.
- Retorno: `products` (id, título, categoria, preço, estoque, pedido mínimo, disponibilidade) e `total`. Lista vazia não é erro.

### `detalhar_produto(id)`

Devolve um produto com marca e descrição. Id inexistente vira erro da tool ("Produto N não existe no catálogo").

### `criar_requisicao(items, missing, message, max_unit_price, request_text, idempotency_key)`

Grava a requisição. É a única tool que escreve (`read_only_hint=False`, `idempotent_hint=True`).

| Argumento | Quem preenche | Regra |
|---|---|---|
| `items` | modelo | 1 a 20 itens `{product_id, quantity}` |
| `missing` | modelo | Itens não atendidos e o motivo |
| `message` | modelo | Resumo curto para o usuário |
| `max_unit_price` | modelo | Orçamento por unidade em USD, ou `null` |
| `request_text` | backend | Texto original do pedido (escondido do modelo) |
| `idempotency_key` | backend | Chave do pedido (escondida do modelo) |

O que acontece (`SubmitRequisitionUseCase`):

1. Soma as quantidades de itens repetidos com o mesmo id.
2. Busca cada id na DummyJSON (`GET /products/{id}`) para pegar título, categoria, preço, estoque e pedido mínimo **reais**.
3. Envia tudo ao backend em `POST /internal/requisicoes` com `X-Internal-Token` (`BackendRequisitionRegistry`).
4. Devolve `requisition_id`, `status`, `total` e `replayed`.

## Erros das tools

Toda falha vira `ToolError`, que o modelo lê e usa para decidir o próximo passo. A tradução fica só no `CatalogErrorTranslator`.

| Situação | Erro de domínio | Mensagem ao modelo |
|---|---|---|
| DummyJSON fora, lenta, 5xx ou payload inesperado | `CatalogUnavailableError` | "Catálogo indisponível... Não invente produtos" |
| Id inexistente | `ProductNotFoundError` | "Produto N não existe no catálogo." |
| Backend recusou (regra violada, 422) | `RequisitionRejectedError` | "Requisição recusada, nada foi gravado: ... Corrija ... ou mova o item para missing." |
| Backend fora ou outro erro | `RequisitionRegistryUnavailableError` | "Não foi possível gravar a requisição... Não diga ao usuário que ela foi criada." |
| Argumento inválido (ex.: categoria fora da lista) | validação do SDK | Erro de validação com os valores aceitos |

## Adapter da DummyJSON

- `DummyJsonHttpClient`: um `httpx.AsyncClient` por processo, timeout de `DUMMYJSON_TIMEOUT_S` (5 s).
- Retry com backoff exponencial (`DUMMYJSON_MAX_ATTEMPTS`, padrão 3; backoff 0,3 s, 0,6 s...) **só** em timeout, erro de conexão e 5xx. 4xx volta direto.
- `DummyJsonProductMapper`: camada anticorrupção; converte o formato externo (camelCase, `price` float) em `Product` (com `Money` em `Decimal`).
- `ProductCategory`: as 24 categorias de `GET /products/category-list`, fixas no código.

## Estrutura

```
mcp-server/src/catalog_mcp/
├── main.py                       # Application: composition root, Streamable HTTP, allowlist de hosts
├── schemas/                      # pricing, product, tools, requisition, dummyjson, health, settings
├── domain/
│   ├── errors/                   # CatalogError e subclasses
│   └── ports/                    # ProductCatalog, RequisitionRegistry
├── application/                  # SearchProducts, GetProductDetail, SubmitRequisition
├── infrastructure/
│   ├── dummyjson/                # cliente HTTP com retry, mapper, catálogo
│   └── backend/                  # BackendRequisitionRegistry (endpoint interno)
└── interfaces/mcp/
    ├── tools/                    # uma classe por tool
    ├── errors/                   # CatalogErrorTranslator
    ├── routes/                   # GET /health
    └── server_factory.py         # monta o servidor com as três tools
```

## Configuração

| Variável | Padrão | Uso |
|---|---|---|
| `INTERNAL_API_TOKEN` | obrigatória (mín. 16) | Token enviado ao endpoint interno do backend |
| `BACKEND_URL` | `http://backend:8000` | Onde gravar as requisições |
| `DUMMYJSON_TIMEOUT_S` | 5 | Timeout por tentativa na DummyJSON |
| `DUMMYJSON_MAX_ATTEMPTS` | 3 | Tentativas em falhas transitórias |
| `BACKEND_TIMEOUT_S`* | 10 | Timeout da chamada ao backend |
| `SEARCH_LIMIT`* | 10 | Máximo de resultados da busca sem categoria |

\* Aceitas pelo `Settings`, mas não repassadas pelo `mcp-server/compose.yml`; para mudar, acrescente-as ao `environment` do serviço.

**Armadilha conhecida:** sem `mcp-server` na allowlist de hosts, o backend recebe **421 Misdirected Request** ao chamar `http://mcp-server:8000/mcp`.
