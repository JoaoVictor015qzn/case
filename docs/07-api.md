# API HTTP

Base: `http://localhost:8000`. JSON em **camelCase**. Dinheiro sempre como `{"amount": "1999.99", "currency": "USD"}` (valor em texto, para não perder precisão). Documentação interativa em `/docs`.

## `POST /requisicoes`

Cria uma requisição a partir de um pedido em texto.

**Headers**

| Header | Obrigatório | Uso |
|---|---|---|
| `Content-Type: application/json` | sim | |
| `Idempotency-Key` | não (máx. 100) | Reenviar com a mesma chave devolve a requisição já criada (200) sem rodar o agente |
| `X-Request-ID` | não | Correlation id; devolvido na resposta e presente nos logs |

**Corpo**

```json
{ "requestText": "Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada." }
```

`requestText`: de 3 a 1000 caracteres.

**201 Created** (ou **200** em replay)

```json
{
  "requisition": {
    "id": 7,
    "requestText": "Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada.",
    "status": "complete",
    "items": [
      {
        "productId": 81,
        "title": "Lenovo Yoga 920",
        "unitPrice": { "amount": "1099.99", "currency": "USD" },
        "quantity": 3,
        "lineTotal": { "amount": "3299.97", "currency": "USD" }
      }
    ],
    "total": { "amount": "3299.97", "currency": "USD" },
    "message": "Requisição nº 7 criada com 3 Lenovo Yoga 920.",
    "missing": [],
    "createdAt": "2026-11-11T14:02:11.123456Z"
  },
  "message": "Requisição nº 7 criada com 3 Lenovo Yoga 920.",
  "missing": [],
  "toolCalls": [
    { "name": "buscar_produtos", "arguments": { "termo": "laptop" }, "isError": false, "durationMs": 412 },
    { "name": "criar_requisicao", "arguments": { "items": [{ "product_id": 81, "quantity": 3 }], "missing": [], "message": "...", "max_unit_price": 2000 }, "isError": false, "durationMs": 655 }
  ],
  "replayed": false
}
```

`status` é `complete` (tudo atendido) ou `partial` (parte foi para `missing`). Os valores do exemplo são ilustrativos.

**Erros**: sempre no formato abaixo; `detail` é texto em português pronto para exibir.

```json
{ "detail": "Nenhum produto do catálogo atende o pedido. Nada foi salvo.", "missing": ["Ferrari: não existe no catálogo."], "toolCalls": [ ... ] }
```

No 422 de pedido não atendível, `detail` é a mensagem que o agente escreveu para o usuário (ou o texto padrão acima, se ele não escreveu nenhuma).

| Status | Quando |
|---|---|
| 422 | Nada do pedido pode ser atendido (com `missing` e `toolCalls`), ou corpo inválido |
| 409 | Corrida com a mesma `Idempotency-Key` sem requisição recuperável |
| 502 | Falha do LLM (chave, crédito, modelo, resposta inválida, limite de rodadas) ou o modelo não gravou |
| 503 | Servidor MCP ou DummyJSON indisponível |
| 504 | O LLM demorou mais que `LLM_TIMEOUT_S` |
| 500 | Erro inesperado (sem detalhes internos na resposta) |

## `GET /requisicoes`

Lista as requisições mais recentes primeiro (até `REQUISITIONS_LIST_LIMIT`, padrão 50). Cada item tem o mesmo formato de `requisition` acima.

## `GET /health`

`{"status": "ok"}`. Usado pelo healthcheck do compose.

## `POST /internal/requisicoes` (interno)

Chamado **só** pelo servidor MCP, na tool `criar_requisicao`. Fora do OpenAPI.

**Header obrigatório**: `X-Internal-Token: <INTERNAL_API_TOKEN>`. Sem ele, ou com valor errado: **401**.

**Corpo**

```json
{
  "requestText": "2 macbooks",
  "idempotencyKey": "6f1c...",
  "items": [
    {
      "productId": 78,
      "title": "Apple MacBook Pro 14 Inch Space Grey",
      "category": "laptops",
      "unitPrice": { "amount": "1999.99", "currency": "USD" },
      "stock": 24,
      "minimumOrderQuantity": 1,
      "quantity": 2
    }
  ],
  "maxUnitPrice": "2000",
  "missing": [],
  "message": "Requisição montada."
}
```

| Status | Quando |
|---|---|
| 201 | Gravada; corpo igual ao do `POST /requisicoes`, com `toolCalls` vazio |
| 200 | `idempotencyKey` já existia (`replayed: true`) |
| 401 | Token ausente ou inválido |
| 422 | Regra violada (estoque, pedido mínimo, orçamento, quantidade) ou campo inválido; `detail` explica o motivo, que o MCP repassa ao modelo |

## Pelo BFF do chat

O frontend expõe `POST` e `GET` em `http://localhost:3000/api/requisicoes`, com o mesmo contrato. Se o backend estiver fora, responde **502**; se passar de `BACKEND_TIMEOUT_MS`, **504**, ambos com `detail`.
