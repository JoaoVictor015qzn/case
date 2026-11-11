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
| `domain/ports/purchasing_agent.py` | `PurchasingAgent` (ABC) | `async def run(request: AgentRequest) -> AgentRun` |
| `domain/ports/catalog_tools_gateway.py` | `CatalogToolsGateway` (ABC) | `list_tools()`, `call_tool(name, arguments)` |
| `domain/services/grounding_validator.py` | `GroundingValidator` | `validate(candidates)`: estoque, pedido mínimo, orçamento |
| `domain/services/requisition_factory.py` | `RequisitionFactory` | monta o agregado a partir da `RequisitionRegistration` validada |
| `application/create_requisition_use_case.py` | `CreateRequisitionUseCase` | roda o agente e busca pela chave o que a tool gravou (nada gravado → 422 ou 502) |
| `application/register_requisition_use_case.py` | `RegisterRequisitionUseCase` | endpoint interno: valida e grava, ou recusa sem gravar |
| `infrastructure/llm/create_requisition_tool_policy.py` | `CreateRequisitionToolPolicy` | esconde e injeta `request_text`/`idempotency_key`; recusa ids não observados |
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
    # Implementado: gateway (CatalogToolsGateway) novo por request, injetado pelo provider;
    # também recebe ProductSnapshotMapper, OpenAIErrorTranslator, model e max_iterations.
    def __init__(self, client: AsyncOpenAI, gateway: CatalogToolsGateway,
                 converter: McpToolSchemaConverter, ...) -> None: ...

    async def run(self, request: AgentRequest) -> AgentRun:
        async with self._gateway as gateway:
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

## Armadilhas confirmadas na implementação

- O `mcp.Client` roda num task group do anyio: **qualquer exceção levantada dentro do `async with` sai embrulhada em `ExceptionGroup`**. O `McpToolsGateway.__aexit__` desembrulha e re-levanta o erro original, para que o `DomainError` chegue intacto ao handler HTTP. Há teste para isso.
- `openai` 3.x e `mcp` 2.x usam **`httpx2`**, não `httpx`. Nos testes, `httpx2.MockTransport` simula a OpenRouter (`tests/fakes/scripted_openrouter.py`).
- Em `strict`, um `$ref` não pode ter `description` ao lado (recusado pelo provider Azure). Enum vai sem `description` no campo; o texto fica na docstring do enum.
- As tools vão com `strict: False`: o schema do MCP não tem `additionalProperties: false`.
- Tools devem devolver `minimum_order_quantity` já na busca: o agente raramente chama `detalhar_produto`.

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

## Gravação: só a tool `criar_requisicao` grava (Fase 13)

1. O modelo chama `criar_requisicao(items=[{product_id, quantity}], missing, message, max_unit_price)`. Ele **não** vê `request_text` nem `idempotency_key`: o `McpToolSchemaConverter` tira esses campos do schema, e o `ToolCallExecutor` os injeta (sobrescrevendo o que o modelo mandar), via `CreateRequisitionToolPolicy`.
2. Defesa em profundidade: se algum id não apareceu nas buscas desta conversa, o executor devolve erro ao modelo **sem chamar o MCP**.
3. O MCP busca cada id na DummyJSON e envia título, preço, estoque e pedido mínimo reais para `POST /internal/requisicoes` (header `X-Internal-Token`).
4. `RegisterRequisitionUseCase`: chave repetida → replay; qualquer violação no `GroundingValidator` → `RequisitionRejectedError` (422, nada gravado; o motivo volta ao modelo para corrigir ou mover para `missing`).
5. Depois do loop, `CreateRequisitionUseCase` procura a requisição pela chave. Achou → 201 com `tool_calls`. Draft `unfulfillable` → 422 com `missing`. O modelo disse que criou e nada foi gravado → `RequisitionNotSavedError` (502).

## Grounding (anti-invenção): `GroundingValidator`, no domínio, não no LLM

- Preço, título, estoque e pedido mínimo vêm **da DummyJSON via MCP**, nunca do modelo.
- `minimum_order_quantity <= quantity <= stock`, e `unit_price <= max_unit_price` quando houver orçamento (`Budget`).
- Os totais são calculados pelo agregado `Requisition` com `Decimal`.
- Status: `partial` se houver `missing`, senão `complete`.

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
| Modelo afirmou sucesso sem gravar | `RequisitionNotSavedError` | 502, com `toolCalls` |
| Endpoint interno: regra violada | `RequisitionRejectedError` | 422 (o MCP repassa o motivo ao modelo) |

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
