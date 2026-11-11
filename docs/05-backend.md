# Backend (contexto Compras)

Pasta `backend/`. API FastAPI em `http://localhost:8000` (docs em `/docs`) com o agente de compras, o grounding e a persistência.

## Estrutura

```
backend/app/
├── main.py                        # Application: composition root, lifespan, logging
├── schemas/                       # pricing, product, requisition, agent, grounding, tools, api, settings, health
├── domain/
│   ├── errors/                    # DomainError + um erro por arquivo (user_message em pt-BR)
│   ├── ports/                     # PurchasingAgent, CatalogToolsGateway, RequisitionRepository, UnitOfWork
│   └── services/                  # GroundingValidator (+ regras), RequisitionFactory
├── application/                   # CreateRequisition, RegisterRequisition, ListRequisitions
├── infrastructure/
│   ├── llm/                       # agente, prompt, executor de tool calls, política, conversor, erros do SDK
│   ├── mcp/                       # McpToolsGateway (cliente MCP)
│   └── persistence/               # tabelas, mapper, repositório, Unit of Work, migrations
└── interfaces/http/
    ├── routes/                    # /requisicoes, /internal/requisicoes, /health
    ├── dependencies/              # providers com Depends, InternalTokenGuard
    ├── errors/                    # DomainErrorHandler, validação, erro inesperado
    └── middleware/                # X-Request-ID (correlation id)
```

## O agente

`OpenRouterPurchasingAgent` implementa um loop próprio de tool calling, sem framework, sobre a Responses API da OpenRouter:

1. Abre a sessão MCP (`McpToolsGateway`) e lista as tools.
2. Converte cada tool para o formato *function* (`McpToolSchemaConverter`), escondendo `request_text` e `idempotency_key` da `criar_requisicao`.
3. Envia o pedido, o prompt de sistema e as tools ao modelo, pedindo a saída final em `json_schema` strict (`RequisitionDraft`).
4. Enquanto o modelo pedir tools, o `ToolCallExecutor` executa cada `function_call` no MCP, registra o trace e devolve o resultado ao modelo.
5. Para quando o modelo responde sem pedir tools, ou levanta `AgentIterationLimitError` depois de `AGENT_MAX_ITERATIONS` rodadas (padrão 8).

O `ToolCallExecutor`, com a `CreateRequisitionToolPolicy`:

- guarda os ids de produtos que apareceram em `buscar_produtos` e `detalhar_produto`;
- recusa `criar_requisicao` com ids que não apareceram, **sem chamar o MCP**;
- injeta `request_text` e `idempotency_key`, sobrescrevendo qualquer valor que o modelo mande;
- devolve JSON inválido nos argumentos como erro para o modelo corrigir, sem interromper o loop.

O prompt de sistema (`SystemPrompt`, versionado em `VERSION`) fica em `infrastructure/llm/system_prompt.py`. Ele orienta a traduzir termos, buscar pela marca, tentar a categoria antes de desistir, respeitar estoque, pedido mínimo e orçamento, chamar `criar_requisicao` uma vez e nunca inventar produto, id ou preço.

## Grounding

`GroundingValidator` aplica quatro regras (padrão Strategy) a cada item, com os dados reais que o MCP enviou:

| Regra | Recusa quando |
|---|---|
| `PositiveQuantityRule` | quantidade < 1 |
| `StockRule` | quantidade > estoque |
| `MinimumOrderQuantityRule` | quantidade < pedido mínimo do produto |
| `BudgetRule` | preço unitário > `max_unit_price` |

Qualquer violação recusa a requisição inteira (422) e nada é gravado. O motivo volta ao modelo pela tool.

## Casos de uso

| Caso de uso | Entrada | O que faz |
|---|---|---|
| `CreateRequisitionUseCase` | `POST /requisicoes` | Replay se a `Idempotency-Key` já existe; senão gera uma chave, roda o agente e procura no banco a requisição gravada com ela. Achou → 201. Draft `unfulfillable` → 422 com o que faltou. Nada gravado → 502 |
| `RegisterRequisitionUseCase` | `POST /internal/requisicoes` | Replay pela chave; grounding; `RequisitionFactory` monta o agregado (status `partial` se houver itens faltando, senão `complete`); grava. Corrida de chave duplicada devolve a existente |
| `ListRequisitionsUseCase` | `GET /requisicoes` | Lista as mais recentes (até `REQUISITIONS_LIST_LIMIT`, padrão 50) |

A persistência é síncrona (SQLModel) e roda fora do event loop com `asyncify`.

## Modelo de domínio

- `Requisition` (aggregate root): itens, status, mensagem, o que faltou, chave; calcula o total e não aceita o mesmo produto duas vezes.
- `RequisitionItem`: snapshot do produto (id, título, preço) + quantidade + subtotal.
- `Money`: `Decimal` + moeda (`USD`), serializado como `{"amount": "1999.99", "currency": "USD"}`.
- `Budget`: teto por unidade.

## Erros → HTTP

Um único `DomainErrorHandler` traduz erros de domínio em respostas no formato `{detail, missing, toolCalls}`.

| Erro | HTTP | Quando |
|---|---|---|
| `RequisitionNotFulfillableError` | 422 | Nada do pedido pode ser atendido (com `missing` e `toolCalls`) |
| `RequisitionRejectedError` | 422 | Endpoint interno: regra de grounding violada |
| `DuplicateIdempotencyKeyError` | 409 | Corrida de chave sem requisição recuperável |
| `RequisitionNotSavedError` | 502 | O modelo terminou sem gravar |
| `LLMConfigurationError` | 502 | Chave recusada (401), sem crédito (402) ou modelo inválido |
| `LLMUnavailableError` | 502 | OpenRouter fora ou 5xx |
| `AgentOutputError` | 502 | Resposta final fora do schema |
| `AgentIterationLimitError` | 502 | Loop passou do limite de rodadas |
| `ToolsUnavailableError` / `CatalogUnavailableError` | 503 | MCP ou catálogo fora |
| `LLMTimeoutError` | 504 | Modelo demorou mais que `LLM_TIMEOUT_S` |
| Corpo inválido | 422 | Texto com menos de 3 ou mais de 1000 caracteres |
| Erro inesperado | 500 | Sem stack trace na resposta; detalhe só no log |

## Observabilidade

- Todo log leva o correlation id (`X-Request-ID` recebido do chat ou gerado), devolvido na resposta.
- Erros de domínio são logados com tipo, status e detalhe; falhas do LLM incluem a dica "verifique OPENROUTER_API_KEY".
