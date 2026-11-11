# Roadmap — Agente de compras

**Entrega:** quarta, 11/11, às 17h, em `.zip` com a pasta `.git`.
**Branch de trabalho:** `develop` (merge na `main` no fim).
**Regra:** nenhum commit, push, exclusão ou mudança de estrutura sem aprovação.

Legenda: ✅ feito · 🟡 em andamento / feito sem commit · ⬜ falta · ⭐ opcional (diferencial)

## Visão geral

| Peça | Status | Observação |
|---|---|---|
| Setup do repositório | ✅ | Commitado na `develop` |
| Skills do Cursor | ✅ | DDD + schemas + compose por serviço, commitadas |
| Servidor MCP | ✅ | 19 testes, ruff e ty verdes; e2e com a DummyJSON real; commitado |
| Postgres + pgAdmin | ✅ | Sobem saudáveis com o mcp-server; pgAdmin importa o servidor `compras` |
| Validação do modelo na OpenRouter | ✅ | `openai/gpt-4.1-mini` aceita tools + `json_schema` strict; commitado |
| Backend (FastAPI + agente) | 🟡 | Fases 3–6 commitadas; HTTP e Docker prontos sem commit (69 testes; `POST /requisicoes` real OK) |
| Chat (Next.js) | 🟡 | Pronto sem commit; sobe no compose e passa pelo BFF; falta o teste manual no navegador |
| CI | ⬜ | |
| Script de evals | ⬜ | |
| README | ⬜ | Hoje está vazio (commit inicial do GitHub) |
| Entrega | ⬜ | |

## Requisitos obrigatórios do case

| Requisito | Status | Onde |
|---|---|---|
| `docker compose up` sobe as quatro peças | ✅ | db, pgadmin, mcp-server, backend e frontend saudáveis (falta conferir em clone limpo) |
| Tabelas criadas automaticamente ao subir | ✅ | `prestart.sh` roda `alembic upgrade head` no start do backend |
| O modelo decide quando chamar cada ferramenta | ✅ | Loop do `OpenRouterPurchasingAgent`, exposto em `POST /requisicoes` |
| DummyJSON falhou ou demorou → mensagem clara no chat | ✅ | MCP (timeout, retry) → backend 503/504 → BFF → chat com `detail` |
| Um teste por ferramenta do MCP, sem chave de LLM | ✅ | `mcp-server/tests/interfaces/` |
| README com como rodar e principais decisões | ⬜ | |

## Diferenciais

| Diferencial | Status | Plano |
|---|---|---|
| Ferramentas chamadas aparecendo no chat | ✅ | `toolCalls` na resposta da API (inclusive no 422) + `ToolCallList` no chat |
| Script com 5 pedidos de teste | ⬜ | `backend/evals/` |
| CI com lint e testes | ⬜ | GitHub Actions rodando os mesmos containers `*-tests` |
| ⭐ Terceira tool `criar_requisicao` | ⬜ | Só se sobrar tempo; precisa de decisão de design |

---

## Fase 0 — Setup ✅

- [x] Branch `develop` criada a partir da `main`
- [x] `.gitignore` (segredos, PDF, `docs/`, caches)
- [x] `.gitattributes` (LF para `.sh` e `Dockerfile`)
- [x] `.env.example` com todas as variáveis
- [x] `.env` local criado a partir do exemplo
- [x] `OPENROUTER_API_KEY` colada no `.env` (usuário)
- [x] `pgadmin/servers.json`, `pgadmin/compose.yml` e `db/compose.yml`
- [x] Skills atualizadas para a estrutura nova
- [x] Autor do repositório configurado com `--local`: `JoaoVictor015qzn <joaovictorsz1230@gmail.com>`
- [x] Commits: 89 (setup + MCP), 66 (fases 2 e 3) e 59 (fases 4 a 6), um por arquivo, Conventional Commits em português, sem coautor
- [x] Verificado após cada lote: autor único `JoaoVictor015qzn`, nenhum segredo e nenhum `.env` no histórico
- [x] Verificado: `docker compose up` sobe db (Postgres 18.6), pgadmin (servidor `compras` importado) e mcp-server, todos saudáveis
- [x] Push da `develop` feito pelo usuário (local = `origin/develop`, 215 commits)

## Fase 1 — Servidor MCP ✅

- [x] `schemas/` por assunto: `pricing`, `product`, `tools`, `dummyjson`, `health`, `settings`
- [x] `domain/`: erros e port `ProductCatalog`
- [x] `application/`: `SearchProductsUseCase`, `GetProductDetailUseCase`
- [x] `infrastructure/dummyjson/`: cliente HTTP (timeout + retry com backoff), mapper anticorrupção, catálogo
- [x] `interfaces/mcp/`: `SearchProductsTool`, `ProductDetailTool`, `CatalogErrorTranslator`, `HealthRoute`, `CatalogMcpServerFactory`
- [x] `main.py` (`Application`: composition root, Streamable HTTP stateless, allowlist de hosts)
- [x] Dockerfile multi-stage (`base` / `test` / `runtime`) e `mcp-server/compose.yml`
- [x] 19 testes, ruff e ty verdes via `docker compose --profile test run --rm mcp-server-tests`
- [x] Teste ponta a ponta pelo compose contra a DummyJSON real
- [x] Commits
- [x] Testes repetidos a partir do estado commitado: 19 passando
- [x] `minimum_order_quantity` incluído no resultado de `buscar_produtos` para o grounding (commitado)

## Fase 2 — Validar o modelo na OpenRouter ✅

- [x] Loop curto com as tools reais do MCP + `text.format` `json_schema` `strict` em `openai/gpt-4.1-mini` (provider Azure, `require_parameters`)
- [x] Primeira tentativa recusada: `$ref cannot have keywords {'description'}` no campo `status`. Corrigido (descrição foi para a docstring do enum) e coberto por teste
- [x] Schema aceito depois do ajuste (`anyOf` de `float | None` e `$defs` funcionam)
- [x] Modelo `openai/gpt-4.1-mini` já fixado no `.env.example`
- [x] Medido: 2–7 s e ~0,7–1,7 mil tokens de entrada por pedido
- [x] Resultado dos 3 pedidos:
  - "2 notebooks até US$ 1500": traduziu para `laptop` e o grounding aceitou
  - "1 ferrari": respondeu sem chamar nenhuma tool (ajustar o prompt na Fase 6)
  - "3 Samsung + 1 mouse": o modelo **inventou o id 201** e o grounding descartou
- [x] Commit

## Fase 3 — Backend: schemas e domínio ✅

- [x] `schemas/pricing/`: `Money`, `Currency`, `Budget`
- [x] `schemas/product/`: `ProductSnapshot`
- [x] `schemas/requisition/`: `Requisition` (aggregate root, calcula total, sem produto repetido), `RequisitionItem`, `RequisitionStatus`
- [x] `schemas/agent/`: `DraftStatus`, `DraftItem`, `RequisitionDraft`, `ToolCallTrace`, `AgentRun`
- [x] `schemas/grounding/`: `GroundingCandidate`, `GroundingResult` (não estava no plano)
- [x] `schemas/settings/`: `Settings`
- [x] `domain/errors/`: `DomainError` + um erro por arquivo, com `user_message` em pt-BR
- [x] `domain/ports/`: `PurchasingAgent`, `RequisitionRepository`, `UnitOfWork` (`CatalogToolsGateway` ficou para a Fase 6, junto do adapter)
- [x] `domain/services/`: `GroundingValidator`, `RequisitionFactory` e regras de grounding como Strategy (`PositiveQuantityRule`, `StockRule`, `MinimumOrderQuantityRule`, `BudgetRule`)
- [x] `pyproject.toml`, `requirements*.txt`, `Dockerfile` (por enquanto só `base` e `test`), `.dockerignore`, `compose.yml` com `backend-tests` e `include` na raiz
- [x] 25 testes, ruff e ty verdes via `docker compose --profile test run --rm backend-tests`
- [x] Commit

## Fase 4 — Backend: casos de uso ✅

- [x] `CreateRequisitionUseCase` (agente → grounding → factory → Unit of Work; persistência síncrona via `asyncify`)
- [x] Idempotency key: chave repetida devolve a requisição existente sem rodar o agente; corrida entre dois requests com a mesma chave vira `DuplicateIdempotencyKeyError` e também devolve a existente
- [x] `ListRequisitionsUseCase`
- [x] `CreatedRequisition` em `schemas/requisition/` (requisição + `tool_calls` + `replayed`)
- [x] Fakes: `FakePurchasingAgent`, `InMemoryUnitOfWork`, `InMemoryRequisitionRepository`
- [x] Testes: criado, nada atende, item não observado, preço do snapshot, idempotência, erro do agente não salva nada
- [x] Commit

## Fase 5 — Backend: persistência ✅

- [x] `Database`, `RequisitionTable`, `RequisitionItemTable`, `RequisitionTableMapper`
- [x] `SqlModelRequisitionRepository` (`selectinload`, sem N+1), `SqlModelUnitOfWork`
- [x] `DatabaseSettings` separado: o Alembic roda sem exigir a chave da OpenRouter (`Settings` herda dele)
- [x] Alembic (`alembic.ini`, `env.py` em classe, `script.py.mako` com `sqlmodel.sql.sqltypes`)
- [x] Migration autogerada e revisada: `requisition_id` virou `NOT NULL` e o `downgrade` remove o enum
- [x] Conferida no Postgres real: `upgrade` → `alembic check` sem diferenças → `downgrade` → `upgrade`
- [x] Repositório conferido no Postgres real (JSONB, enum, `NUMERIC`, chave única → `DuplicateIdempotencyKeyError`)
- [x] `scripts/prestart.sh` com `alembic upgrade head` (LF, senão quebra no container)
- [x] Testes com SQLite in-memory
- [x] Commit

## Fase 6 — Backend: agente ✅

- [x] Port `CatalogToolsGateway` + schemas `ToolDefinition`, `ToolResult`, `CatalogProductPayload` em `schemas/tools/`
- [x] `McpToolsGateway` (cliente MCP v2, timeout, falha de conexão → `ToolsUnavailableError`, desembrulha o `ExceptionGroup` do anyio)
- [x] `McpToolSchemaConverter`, `ProductSnapshotMapper`, `ToolCallExecutor`, `OpenAIErrorTranslator`
- [x] `SystemPrompt` (pt-BR, tradução, termos curtos, sempre buscar antes de dizer "não encontrado", quantidade mínima)
- [x] `OpenRouterPurchasingAgent` (loop, limite de iterações, saída estruturada strict, `require_parameters`)
- [x] Testes sem rede: OpenRouter simulada com `httpx2.MockTransport`, MCP em memória, gateway falso
- [x] Smoke real (agente + MCP + OpenRouter + Postgres): notebooks ✅, ferrari → nada salvo (agora busca antes) ✅, Samsung + mouse → parcial com produto real ✅, idempotência ✅, MCP fora → `ToolsUnavailableError` ✅, modelo inválido → `LLMConfigurationError` ✅
- [x] Commit

## Fase 7 — Backend: HTTP 🟡

- [x] `schemas/api/` com `ApiModel` (JSON em camelCase): `CreateRequisitionRequest`, `RequisitionCreatedResponse`, `RequisitionPublic`, `RequisitionItemPublic`, `ToolCallPublic`, `ErrorResponse`; `schemas/health/HealthStatus`
- [x] `RequisitionsRouter` (`POST` 201 / replay 200, `GET /requisicoes`, header `Idempotency-Key`), `HealthRouter`
- [x] `DomainErrorHandler` (409/422/502/503/504), `RequestValidationErrorHandler` (422 em texto), `UnexpectedErrorHandler` (500 sem stack), `CorrelationIdMiddleware` (`X-Request-ID` no log e na resposta)
- [x] Providers em `interfaces/http/dependencies/` (agente e gateway MCP por request; `AsyncOpenAI` e `Database` no lifespan via `ApplicationResources`)
- [x] `main.py` (`Application`: composition root, lifespan, logging com correlation id)
- [x] 9 testes com `TestClient` + `dependency_overrides` (69 no total), ruff e ty verdes
- [ ] Commit

## Fase 8 — Integração com Docker (marco principal) 🟡

- [x] Estágio `runtime` no `backend/Dockerfile` (não-root, `prestart.sh` + `fastapi run`) e serviço `backend` no `backend/compose.yml` (fail-fast, `depends_on` saudável, healthcheck)
- [x] `include` do backend no `compose.yml` da raiz
- [x] `docker compose up --build`: db, pgadmin, mcp-server, backend e frontend saudáveis
- [x] Tabelas conferidas no Postgres (acentos corretos, preço vindo do catálogo); falta só olhar no pgAdmin
- [x] **Pedido de exemplo funcionando via `POST /requisicoes`**: 2× Huawei Matebook X Pro, USD 2.799,98; replay com a mesma chave → 200 `replayed`
- [x] Derrubar o mcp-server → 503 com mensagem clara
- [x] Porta 8000 ocupada por outro projeto do usuário (`med-lambda-orchestrator-fastapi-gateway-1`): parado com aprovação
- [ ] Commit

## Fase 9 — Chat (Next.js) 🟡

- [x] Estilo decidido: componentes como funções, lógica em classes
- [x] Next 16.4.6 + React 19.3 (`create-next-app`, sem Tailwind, CSS simples)
- [x] Route Handler BFF (`/api/requisicoes`) com `BackendProxy` (timeout, repassa `Idempotency-Key`/`X-Request-ID`, rede → 502/504 com `detail`)
- [x] Classes: `RequisitionsClient`, `ErrorMessageTranslator`, `MoneyFormatter`, `ChatMessageFactory`; tipos em `lib/types/`, um por arquivo
- [x] Chat com estados: enviando, sucesso (Requisição nº, itens, total), 422 (o que falta), 5xx (`detail`)
- [x] `ToolCallList` (diferencial) e `MissingList`
- [x] Dockerfile standalone e `frontend/compose.yml`, incluídos na raiz
- [x] `npm run lint`, `tsc` e `npm run build` (no Docker) verdes
- [x] Conferido pelo BFF: parcial (3× Galaxy S7 + mouse em falta) 201, ferrari 422, MCP fora 503, backend fora 502
- [x] Prompt v2026-11-10.2: buscar pela marca e tentar outro termo quando o resultado não traz o item (antes, "smartphones Samsung" virava 422)
- [ ] Teste manual no navegador (http://localhost:3000)
- [ ] Commit

## Fase 10 — CI e evals ⬜

- [ ] `.github/workflows/ci.yml`: containers `*-tests`, lint/build do frontend, `docker compose config`
- [ ] `backend/evals/` com os 5 casos (exemplo, notebook → laptop, smartphones, Ferrari, orçamento impossível)
- [ ] Conferir as expectativas contra o catálogo real
- [ ] Rodar e registrar o placar

## Fase 11 — README ⬜

- [ ] Como rodar (3 passos) e portas (3000, 8000, 5050)
- [ ] Arquitetura (diagrama + DDD em um parágrafo)
- [ ] Principais decisões no formato o quê → por quê → trade-off
- [ ] Testes, evals e placar
- [ ] Uso de IA (Cursor, skills, o que foi revisado e decidido manualmente)
- [ ] Limitações e próximos passos

## Fase 12 — Entrega ⬜

- [ ] Clone limpo → `cp .env.example .env` → chave → `docker compose up --build` → pedido de exemplo OK
- [ ] Nenhum segredo no histórico (`git log -p` sem `sk-or-`)
- [ ] Merge `develop` → `main`
- [ ] `.zip` com a pasta `.git`

## Fase 13 — ⭐ `criar_requisicao` (só se sobrar tempo) ⬜

- [x] Desenho decidido: o MCP chama um endpoint interno do backend (só começa depois do README)
- [ ] Implementar e ajustar o prompt e o grounding

---

## Cronograma sugerido

| Quando | O quê |
|---|---|
| Hoje, até 21h45 | ~~Setup + MCP; validar o modelo; schemas e domínio do backend~~ (feito e commitado) |
| Hoje, 21h45–23h30 | ~~Casos de uso, persistência e agente~~ (feito e commitado) |
| Até ~23h | ~~HTTP, integração Docker e chat Next.js~~ (feito, falta commit; **à frente do plano**) |
| Amanhã, 11h–13h | CI e evals |
| Amanhã, 13h–15h | README e teste em clone limpo |
| Amanhã, 15h–17h | Margem e entrega |

## Decisões tomadas

| Decisão | Por quê | Trade-off |
|---|---|---|
| Python 3.14 nos dois serviços | Stack única, SDK MCP oficial em Python | — |
| pip + `requirements.txt` fixado (sem uv) | Dockerfile simples, build reprodutível | Sem hashes e sem a velocidade do uv |
| DDD tático (contextos Catálogo e Compras) | Domínio claro: agregado, value objects, grounding | Mais arquivos que um projeto plano |
| Pydantic em todo dado, `schemas/` por assunto, uma classe por arquivo | Validação e serialização uniformes; fácil de navegar | O domínio depende do Pydantic |
| Sem framework de agentes | O case exige que o modelo decida; loop explícito é fácil de explicar | Mais código próprio |
| SQLModel + Alembic | Migrations versionadas e automáticas; mesmos tipos do FastAPI | Setup do Alembic |
| Um `compose.yml` por serviço + `include` na raiz | Responsabilidades separadas, `docker compose up` único | Um arquivo a mais por serviço |
| Testes e lint via estágio `test` do Dockerfile | Nada instalado no host; CI igual ao local | Rebuild da camada de código a cada execução |
| pgAdmin com servidor pré-registrado | Inspeção do banco sem configuração manual | Um serviço extra no compose |
| MCP stateless com retry só em falha transitória | Escala horizontal; resiliência a DummyJSON instável | Pior caso ≈ 3 × timeout |
| Um commit por arquivo, rodado pelo usuário no próprio terminal | Histórico granular, sem o coautor que o Cursor injeta nos commits do agente | Histórico longo (214 commits até a Fase 6) |

## Decisões pendentes (consultar o usuário)

- [x] ~~Quando commitar o que já está pronto~~ (feito)
- [x] ~~Como commitar as próximas peças~~: script `.ps1` gerado pelo agente e rodado pelo usuário (usado nos dois lotes)
- [x] ~~Formato do dinheiro na API~~: objeto `{"amount": "1999.99", "currency": "USD"}`, igual ao MCP
- [x] ~~Estilo do frontend~~: componentes como funções (padrão React), lógica em classes (cliente da API, formatadores, tradutor de erros)
- [x] ~~Terceira tool `criar_requisicao`~~: só se sobrar tempo depois do README, com o MCP chamando um endpoint interno do backend
- [x] ~~`buscar_produtos` sem `minimum_order_quantity`~~: campo incluído no resumo da busca (testado e conferido contra a DummyJSON real)

## Riscos

| Risco | Mitigação |
|---|---|
| Provider da OpenRouter rejeitar o schema `strict` | Aconteceu na Fase 2 (`$ref` com `description`); corrigido e coberto por teste |
| Modelo inventar produtos ou responder sem consultar o catálogo | Visto na Fase 2; o grounding descarta ids não observados; o prompt da Fase 6 vai exigir busca antes de "não encontrado" |
| Chave com orçamento limitado | Modelo barato; evals só quando necessário |
| `docker compose up` falhar na máquina do avaliador | Teste em clone limpo; fail-fast no `.env`; healthchecks |
| Prazo | Fluxo completo (Fases 7–9) pronto em 10/11 à noite; restam CI, evals, README e entrega |
| Porta do host ocupada na máquina de quem roda (8000, 3000, 5050) | Documentar no README como liberar a porta |
| Termos em português sem resultado na DummyJSON (`notebook` = 0) | Regra de tradução no prompt + caso nos evals |
