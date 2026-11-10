---
name: agent-loop
description: Implementa o agente de compras do backend - loop de tool calling próprio em classes (OpenRouterPurchasingAgent) com SDK openai apontado para a OpenRouter (Responses API), ferramentas vindas do servidor MCP via McpToolsGateway, prompt de sistema anti-invenção, saída estruturada (json_schema) com schemas Pydantic em schemas/agent e verificação de grounding no GroundingValidator. Use ao escrever ou ajustar o agente, o prompt, a integração OpenRouter/MCP no backend ou ao depurar respostas inventadas.
---

# Agente de compras (OpenRouter + MCP, sem framework)

Exemplos oficiais (OpenRouter e cliente MCP): [reference.md](reference.md). Regras gerais: skill `case-architecture`.

## Por que sem framework

- O case exige que **o modelo decida quando chamar cada ferramenta**. Um loop explícito prova isso e é fácil de explicar na entrevista.
- A OpenRouter documenta exatamente esse padrão ("A Simple Agentic Loop"), e o SDK MCP v2 entrega as tools prontas (`list_tools`/`call_tool`).

## Onde o código mora (uma classe por arquivo)

| Arquivo | Classe | Papel |
|---|---|---|
| `domain/ports/purchasing_agent.py` | `PurchasingAgent` (ABC) | `async def run(request_text) -> AgentRun` |
| `domain/ports/catalog_tools_gateway.py` | `CatalogToolsGateway` (ABC) | `list_tools()`, `call_tool(name, arguments)` |
| `domain/services/grounding_validator.py` | `GroundingValidator` | aplica as regras anti-invenção |
| `domain/services/requisition_factory.py` | `RequisitionFactory` | monta o agregado a partir do draft validado |
| `application/create_requisition_use_case.py` | `CreateRequisitionUseCase` | roda o agente, valida, persiste via Unit of Work |
| `infrastructure/llm/openrouter_purchasing_agent.py` | `OpenRouterPurchasingAgent` | o loop (SDK openai) |
| `infrastructure/llm/system_prompt.py` | `SystemPrompt` | prompt versionado (constante de classe) |
| `infrastructure/llm/mcp_tool_schema_converter.py` | `McpToolSchemaConverter` | tool MCP → formato function da Responses API |
| `infrastructure/llm/tool_call_executor.py` | `ToolCallExecutor` | executa uma `function_call`, registra trace e snapshots |
| `infrastructure/llm/openai_error_translator.py` | `OpenAIErrorTranslator` | exceções do SDK → erros de domínio |
| `infrastructure/mcp/mcp_tools_gateway.py` | `McpToolsGateway` | `mcp.Client`: lista e executa as tools |

Schemas em `schemas/agent/` (Pydantic, `frozen=True`):
- `DraftItem`, `RequisitionDraft`: a saída estruturada do modelo;
- `ToolCallTrace(name, arguments, is_error, duration_ms)`: usado para mostrar as tools no chat;
- `AgentRun(draft, observed_products: dict[int, ProductSnapshot], tool_calls: list[ToolCallTrace])`.

`ProductSnapshot` (em `schemas/product/`) guarda id, título, categoria, `Money` e estoque exatamente como a tool devolveu.

## O loop (Responses API via SDK openai)

```python
class OpenRouterPurchasingAgent(PurchasingAgent):
    def __init__(self, client: AsyncOpenAI, gateway_factory: McpToolsGatewayFactory,
                 converter: McpToolSchemaConverter, settings: Settings) -> None: ...

    async def run(self, request_text: str) -> AgentRun:
        async with self._gateway_factory.connect() as gateway:
            tools = self._converter.convert(await gateway.list_tools())
            executor = ToolCallExecutor(gateway)
            items: list[ResponseInputItemParam] = [{"role": "user", "content": request_text}]
            for _ in range(self._settings.agent_max_iterations):
                response = await self._ask_model(items, tools)
                items += response.output                     # "It's easy to forget this step!"
                calls = [i for i in response.output if i.type == "function_call"]
                if not calls:
                    return executor.finish(RequisitionDraft.model_validate_json(response.output_text))
                for call in calls:
                    items.append(await executor.execute(call))
        raise AgentIterationLimitError(self._settings.agent_max_iterations)

    async def _ask_model(self, items, tools) -> Response:
        response = await self._client.responses.create(
            model=self._settings.openrouter_model,
            instructions=SystemPrompt.TEXT,
            tools=tools,                                     # obrigatório em TODA chamada
            input=items,
            text={"format": RequisitionDraft.response_format()},
            extra_body={"provider": {"require_parameters": True}},
        )
        if response.status != "completed":
            raise LLMUnavailableError(response.error.message if response.error else response.status)
        return response
```

Cliente: `AsyncOpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key.get_secret_value(), timeout=settings.llm_timeout_s, max_retries=2)`. Criado uma vez no lifespan. O SDK respeita `Retry-After` (429/503).

`McpToolSchemaConverter.convert(tools)` devolve `[{"type": "function", "name": t.name, "description": t.description or "", "parameters": t.input_schema}]`.

`ToolCallExecutor.execute(call)`:
1. Faz o parse de `call.arguments`. Se o JSON for inválido, devolve `function_call_output` com o erro para o modelo corrigir.
2. Chama `gateway.call_tool(call.name, args)`, mede `duration_ms` e registra o `ToolCallTrace`.
3. Se `not result.is_error`, extrai os produtos de `result.structured_content` para os snapshots observados (via um mapper que converte o payload da tool em `ProductSnapshot`; `price` vem como `{"amount": "1999.99", "currency": "USD"}`).
4. Retorna `{"type": "function_call_output", "call_id": call.call_id, "output": <texto de result.content>}`.
5. `is_error=True` **não interrompe** o loop: o modelo lê o erro e decide o próximo passo.

## Saída estruturada (o draft)

Modelos com `ConfigDict(extra="forbid", frozen=True)` e todos os campos obrigatórios, o que é necessário para `strict: true`:

```python
class DraftItem(BaseModel):
    product_id: int
    quantity: int
    reason: str

class RequisitionDraft(BaseModel):
    status: Literal["complete", "partial", "unfulfillable"]
    max_unit_price: Decimal | None      # orçamento por unidade extraído do pedido, se houver
    items: list[DraftItem]
    missing: list[str]                  # o que não foi possível atender e por quê
    message: str                        # resposta ao usuário, pt-BR

    @classmethod
    def response_format(cls) -> dict[str, object]:
        return {"type": "json_schema", "name": "requisition_draft", "strict": True,
                "schema": cls.model_json_schema()}
```

Risco conhecido: `X | None` vira `anyOf` e `Field(ge=1)` vira `minimum`, que alguns providers rejeitam em `strict`. Valide o modelo escolhido antes; se rejeitar, simplifique o schema e valide `quantity >= 1` no `GroundingValidator`.

## Grounding (anti-invenção): `GroundingValidator`, no domínio, não no LLM

Para cada `DraftItem`:
1. O `product_id` precisa estar em `observed_products`. Se não estiver, o item é descartado e vai para `missing` ("produto não verificado no catálogo").
2. Preço e título vêm **do snapshot**, nunca do texto do modelo.
3. `1 <= quantity <= stock`, e `unit_price <= max_unit_price` quando houver orçamento (`Budget`). Se a regra for violada, o item é descartado e vai para `missing`.
4. Os totais são calculados pelo agregado `Requisition` com `Decimal`.

Se não sobrar nenhum item válido, levante `RequisitionNotFulfillableError(missing)`. Nesse caso nada é salvo.

## Prompt de sistema (pt-BR, em `SystemPrompt.TEXT`)

```text
Você é um agente de compras corporativas. Monte requisições de compra usando APENAS produtos
retornados pelas ferramentas nesta conversa.

Ferramentas:
- buscar_produtos(termo): busca no catálogo. O catálogo é em inglês: traduza o pedido
  (ex.: "notebook" -> "laptop"). Se não encontrar, tente sinônimos antes de desistir.
- detalhar_produto(id): use para confirmar preço e estoque antes de escolher um item.

Regras:
1. Nunca invente produto, id, preço ou estoque. Se não veio de uma ferramenta, não existe.
2. Respeite quantidade e orçamento pedidos. Preços estão em USD.
3. Se nada atender, retorne status "unfulfillable", items vazio e explique em "missing" o que faltou
   (ex.: "nenhum laptop até US$ 2.000 com 3 unidades em estoque").
4. Se só parte atender, use status "partial" e liste o restante em "missing".
5. Se uma ferramenta falhar, não invente: informe em "missing" que o catálogo está indisponível.
6. "message" é a resposta ao usuário, em português, curta e objetiva.
```

Atenção: a busca `notebook` na DummyJSON retorna 0 resultados e `laptop` retorna 5. A instrução de tradução é crítica.

O prompt é parte do produto e é avaliado ("prompt claro"). Mudanças nele exigem rodar o script de evals (skill `quality-ci`).

## Erros → domínio → HTTP

Classes em `domain/errors/`, uma por arquivo, herdando de `DomainError`. A tradução das exceções do SDK fica no `OpenAIErrorTranslator`.

| Origem | Exceção de domínio | HTTP |
|---|---|---|
| `openai.APITimeoutError` | `LLMTimeoutError` | 504 |
| `openai.APIConnectionError`, `APIStatusError` (5xx, 502/503) | `LLMUnavailableError` | 502 |
| `openai.AuthenticationError` (401) ou 402 (sem créditos) | `LLMConfigurationError` | 502, com log "verifique OPENROUTER_API_KEY" |
| Falha de conexão com o MCP (`httpx2.ConnectError`, `MCPError`) | `ToolsUnavailableError` | 503 |
| JSON inválido no draft (`ValidationError`) | `AgentOutputError` | 502 |
| Estouro de iterações | `AgentIterationLimitError` | 502 |
| Nada atende | `RequisitionNotFulfillableError` | 422, com `missing` |

## Modelo

- Vem de `OPENROUTER_MODEL` (env). Precisa suportar `tools` **e** `structured_outputs`: `https://openrouter.ai/models?supported_parameters=tools,structured_outputs`.
- Default no `.env.example`: `openai/gpt-4.1-mini` (a validar com a chave antes de escrever o loop). Prefira modelo barato e rápido: a chave expira em 7 dias e tem orçamento.

## Checklist

- [ ] Não há chamada de tool hardcoded. Só o modelo decide
- [ ] `tools` vai em toda requisição, e `response.output` é reanexado a `items`
- [ ] Há limite de iterações e timeout no cliente LLM
- [ ] O grounding é verificado no `GroundingValidator`, com preço vindo do snapshot
- [ ] Os `ToolCallTrace` são retornados na resposta da API (diferencial "ferramentas no chat")
- [ ] Os testes do caso de uso usam `FakePurchasingAgent`, sem rede e sem chave
