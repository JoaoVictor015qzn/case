---
name: mcp-server
description: Constrói e testa o servidor MCP do case (tools buscar_produtos, detalhar_produto e criar_requisicao sobre a DummyJSON) com o SDK oficial MCP Python v2 (MCPServer, add_tool com métodos de classe, Streamable HTTP stateless, ToolError, Client in-memory), seguindo DDD com schemas Pydantic por assunto e uma classe por arquivo. Use ao criar ou alterar tools MCP, o adapter da DummyJSON, a configuração de transporte/Host allowlist ou os testes do mcp-server.
---

# Servidor MCP (contexto Catálogo, SDK oficial `mcp` v2)

Exemplos oficiais e as armadilhas da v2: [reference.md](reference.md). Regras gerais: skill `case-architecture`.

## Regras da v2 (não use padrões da v1)

| Use (v2) | Não use (v1, removido) |
|---|---|
| `from mcp.server import MCPServer` | `from mcp.server.fastmcp import FastMCP` |
| `server.add_tool(obj.execute, name=..., title=..., annotations=...)` | tools como funções aninhadas com `@mcp.tool()` |
| `from mcp import Client` (`Client(server)` nos testes) | `create_connected_server_and_client_session()` |
| Opções de transporte em `server.run(...)` | `MCPServer("x", port=...)`, que gera `TypeError` |
| `result.is_error`, `result.structured_content` (snake_case) | `isError`, `structuredContent` |

`add_tool` aceita método de instância: o `self` não aparece no input schema, o nome vem de `name=` e a descrição vem da docstring do método (verificado no `mcp` 2.3.0).

## Estrutura (uma classe por arquivo)

```
mcp-server/src/catalog_mcp/
├── main.py                                   # Application: composition root, run() e lifespan
├── schemas/
│   ├── pricing/currency.py, money.py         # Currency (StrEnum), Money (Decimal + moeda)
│   ├── product/product.py                    # Product (entidade do contexto)
│   ├── tools/product_summary.py              # ProductSummary.from_product
│   ├── tools/product_detail.py               # ProductDetail.from_product
│   ├── tools/search_products_result.py       # SearchProductsResult.from_products
│   ├── tools/tool_arguments.py               # aliases Annotated: SearchTerm, ProductId
│   ├── dummyjson/dummyjson_product.py        # formato externo (camelCase via alias_generator)
│   ├── dummyjson/dummyjson_search_response.py
│   ├── health/health_status.py
│   └── settings/settings.py                  # Settings (pydantic-settings)
├── domain/
│   ├── errors/catalog_error.py               # base
│   ├── errors/catalog_unavailable_error.py
│   ├── errors/product_not_found_error.py
│   └── ports/product_catalog.py              # ProductCatalog (ABC): search(term), get(product_id)
├── application/
│   ├── search_products_use_case.py           # SearchProductsUseCase.execute(term)
│   └── get_product_detail_use_case.py        # GetProductDetailUseCase.execute(product_id)
├── infrastructure/dummyjson/
│   ├── dummyjson_http_client.py              # httpx + timeout + retry com backoff (só transitórios)
│   ├── dummyjson_product_mapper.py           # anticorrupção: DummyJsonProduct -> Product
│   └── dummyjson_product_catalog.py          # implementa ProductCatalog
└── interfaces/mcp/
    ├── server_factory.py                     # CatalogMcpServerFactory(catalog, lifespan).create()
    ├── errors/catalog_error_translator.py    # CatalogError -> ToolError (único ponto)
    ├── tools/mcp_tool.py                     # McpTool (ABC): register(server)
    ├── tools/search_products_tool.py         # SearchProductsTool: buscar_produtos(termo)
    ├── tools/product_detail_tool.py          # ProductDetailTool: detalhar_produto(id)
    └── routes/health_route.py                # HealthRoute: GET /health
```

Fluxo: `Tool.execute` → `UseCase.execute` → `ProductCatalog` (port) → `DummyJsonProductCatalog` → `DummyJsonHttpClient`.

### Busca por categoria

- `buscar_produtos(termo, categoria=None)`: `categoria` é `ProductCategory` (`schemas/product/product_category.py`, as 24 categorias de `GET /products/category-list`). O enum aparece no schema da tool, então o modelo vê os valores válidos.
- Com categoria, `SearchProductsUseCase` chama `ProductCatalog.list_category` (`GET /products/category/{c}?limit=0`, no máximo 30 produtos) e filtra por palavra do termo no título ou na marca. Sem nenhum produto com o termo, devolve a categoria inteira.
- Motivo: buscas traduzidas do português falham quando o modelo não sabe o que existe ("cadeira" → 0; categoria `furniture` → a cadeira que existe).

### Terceira tool: `criar_requisicao` (Fase 13)

- `CreateRequisitionTool` (`read_only=False`, `destructive=False`, `idempotent=True`, `open_world=False`): `execute(items, missing, message, max_unit_price, request_text, idempotency_key)`. Os dois últimos são preenchidos pelo backend e escondidos do modelo.
- `SubmitRequisitionUseCase(catalog, registry)`: soma quantidades do mesmo id, busca cada id com `catalog.get` (preço, estoque e pedido mínimo reais) e registra.
- Port `RequisitionRegistry` → `BackendRequisitionRegistry` (`infrastructure/backend/`): `POST {BACKEND_URL}/internal/requisicoes` com `X-Internal-Token`. 422 → `RequisitionRejectedError` (o motivo volta ao modelo); outros erros ou rede → `RequisitionRegistryUnavailableError` ("não diga ao usuário que ela foi criada").
- Schemas em `schemas/requisition/` (`CamelModel`, `RequisitionSubmission`, `RequisitionSubmissionItem`, `RegisteredRequisition`, `RegistrationResponse`) e `schemas/tools/created_requisition_result.py`.
- `Settings`: `backend_url`, `backend_timeout_s` e `internal_api_token` (obrigatório, mínimo de 16 caracteres).

## Template de uma tool

```python
class SearchProductsTool(McpTool):
    NAME = "buscar_produtos"
    TITLE = "Buscar produtos"

    def __init__(self, use_case: SearchProductsUseCase, errors: CatalogErrorTranslator) -> None:
        self._use_case = use_case
        self._errors = errors

    def register(self, server: MCPServer) -> None:
        server.add_tool(
            self.execute,
            name=self.NAME,
            title=self.TITLE,
            annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
        )

    async def execute(self, termo: SearchTerm) -> SearchProductsResult:
        """Docstring em pt-BR: vira a descrição que o LLM lê."""
        try:
            return await self._use_case.execute(termo)
        except CatalogError as exc:
            raise self._errors.to_tool_error(exc) from exc
```

- O nome do parâmetro do método é o nome do argumento da tool: `termo` e `id`, exatamente como no case.
- Os argumentos usam os aliases `Annotated` de `schemas/tools/tool_arguments.py`, com `Field(description=...)`. Não embrulhe os argumentos num modelo, porque isso mudaria o contrato para `{"input": {...}}`.
- O retorno é sempre um modelo de `schemas/tools/`, o que gera `structured_content`. `Money` serializa como `{"amount": "1999.99", "currency": "USD"}`.
- A factory monta as tools a partir do catálogo, e o `main.py` só escolhe o catálogo real. Os testes usam a mesma factory com um fake.

## Erros: qual exceção levantar

Pergunta da doc oficial: *"um modelo mais esperto teria evitado isso?"* Se sim, use `ToolError`. Se não, use `MCPError`.

| Situação | Domínio | Na tool |
|---|---|---|
| Produto inexistente | `ProductNotFoundError` | `ToolError` com a mensagem |
| DummyJSON fora, timeout, 5xx, payload inesperado | `CatalogUnavailableError` | `ToolError` "Catálogo indisponível: ... Não invente produtos" |
| Busca sem resultado | nenhum | `SearchProductsResult(products=[], total=0)` |
| Bug inesperado | deixe propagar | o modelo vê "Error executing tool", o traceback vai para o log |

- **Nunca `return` uma string de erro.** O retorno teria `is_error=False`.
- **Não revalide os type hints.** O SDK já rejeita argumentos inválidos.
- A tradução domínio → `ToolError` fica só no `CatalogErrorTranslator`.

## Adapter DummyJSON

- `DummyJsonHttpClient.from_settings(settings)` cria **um** `httpx.AsyncClient` por processo, com `base_url` e `timeout` vindos de `Settings`. O `Application._lifespan` fecha o cliente no shutdown.
- Retry com backoff exponencial (`dummyjson_max_attempts`, `dummyjson_retry_backoff_s`) **só** para timeout, erro de conexão e 5xx. 4xx volta direto.
- Endpoints: `GET /products/search?q=&select=&limit=` e `GET /products/{id}`. 404 vira `ProductNotFoundError`.
- O payload é validado com `DummyJsonSearchResponse`/`DummyJsonProduct`. Falha de validação vira `CatalogUnavailableError("resposta inesperada")`.

## Rodando em Docker (Streamable HTTP)

```python
self.build_server().run(
    transport="streamable-http",
    host=settings.host,
    port=settings.port,
    stateless_http=True,
    transport_security=TransportSecuritySettings(allowed_hosts=settings.allowed_hosts),
)
```

**Armadilha crítica:** sem `transport_security` com `mcp-server` e `mcp-server:*` em `allowed_hosts`, o backend chamando `http://mcp-server:8000/mcp` recebe **421 Misdirected Request**, e o motivo só aparece no log do servidor.

Comando do container: `python -m catalog_mcp.main`. Healthcheck: `GET /health` → `HealthStatus`.

## Testes (requisito: um por tool, sem chave de LLM)

```
tests/
├── conftest.py                                # fixtures client / unavailable_client (Client in-memory)
├── fakes/
│   ├── fake_product_catalog.py                # FakeProductCatalog(ProductCatalog)
│   ├── sample_products.py                     # SampleProducts.MACBOOK, LENOVO
│   ├── scripted_transport.py                  # httpx.MockTransport com roteiro de respostas
│   └── tool_result_reader.py
├── interfaces/test_server_factory.py          # list_tools, argumentos obrigatórios, read_only
├── interfaces/test_search_products_tool.py
├── interfaces/test_product_detail_tool.py
├── infrastructure/test_dummyjson_http_client.py   # retry, timeout, conexão, 4xx sem retry
└── infrastructure/test_dummyjson_product_catalog.py
```

- `Client(server, raise_exceptions=True)` in-memory: sem porta, sem subprocess, sem rede.
- `pytestmark = pytest.mark.anyio` e a fixture `anyio_backend` retornando `"asyncio"`.
- Rodar: `docker compose --profile test run --rm mcp-server-tests` (ruff, ty e pytest).

Cobertura mínima: para cada tool, caminho feliz, erro de negócio (vazio/inexistente/argumento inválido) e catálogo indisponível; adapter com 200, 404, 5xx com retry, timeout, conexão e payload inesperado.

## Checklist

- [ ] Uma classe por arquivo; dados em `schemas/`; sem dataclass e sem função solta
- [ ] Os nomes são exatamente `buscar_produtos(termo)`, `detalhar_produto(id)` e `criar_requisicao(items, ...)`
- [ ] Docstring clara em pt-BR no `execute` e `Field(description=...)` em cada argumento
- [ ] Retorno é modelo Pydantic (gera `structured_content`); `read_only_hint=True` nas tools de leitura
- [ ] `transport_security` configurado para o hostname do compose
- [ ] Os testes usam `Client(server)` in-memory e não acessam rede
