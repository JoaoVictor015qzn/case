# Roadmap — Agente de compras

**Entrega:** quarta, 11/11, às 17h, em `.zip` com a pasta `.git`.
**Branch de trabalho:** `develop` (merge na `main` no fim).
**Regra:** nenhum commit, push, exclusão ou mudança de estrutura sem aprovação.

Legenda: ✅ feito · 🟡 em andamento / feito sem commit · ⬜ falta · ⭐ opcional (diferencial)

## Visão geral

| Peça | Status | Observação |
|---|---|---|
| Setup do repositório | 🟡 | Arquivos prontos, nada commitado |
| Skills do Cursor | 🟡 | Atualizadas para DDD + schemas + compose por serviço, sem commit |
| Servidor MCP | 🟡 | Pronto e testado (19 testes, ruff, ty, e2e com a DummyJSON real), sem commit |
| Postgres + pgAdmin | 🟡 | `compose.yml` escritos; ainda não subiram juntos |
| Validação do modelo na OpenRouter | ⬜ | Depende da chave no `.env` |
| Backend (FastAPI + agente) | ⬜ | Próxima peça |
| Chat (Next.js) | ⬜ | |
| CI | ⬜ | |
| Script de evals | ⬜ | |
| README | ⬜ | Hoje está vazio (commit inicial do GitHub) |
| Entrega | ⬜ | |

## Requisitos obrigatórios do case

| Requisito | Status | Onde |
|---|---|---|
| `docker compose up` sobe as quatro peças | ⬜ | `compose.yml` da raiz com `include` (hoje: db, pgadmin, mcp-server) |
| Tabelas criadas automaticamente ao subir | ⬜ | Alembic no `prestart.sh` do backend |
| O modelo decide quando chamar cada ferramenta | ⬜ | Loop do `OpenRouterPurchasingAgent` |
| DummyJSON falhou ou demorou → mensagem clara no chat | 🟡 | MCP pronto (timeout, retry, `ToolError`); falta backend (503/504) e chat |
| Um teste por ferramenta do MCP, sem chave de LLM | ✅ | `mcp-server/tests/interfaces/` (sem commit) |
| README com como rodar e principais decisões | ⬜ | |

## Diferenciais

| Diferencial | Status | Plano |
|---|---|---|
| Ferramentas chamadas aparecendo no chat | ⬜ | `ToolCallTrace` na resposta da API + `ToolCallList` no chat |
| Script com 5 pedidos de teste | ⬜ | `backend/evals/` |
| CI com lint e testes | ⬜ | GitHub Actions rodando os mesmos containers `*-tests` |
| ⭐ Terceira tool `criar_requisicao` | ⬜ | Só se sobrar tempo; precisa de decisão de design |

---

## Fase 0 — Setup 🟡

- [x] Branch `develop` criada a partir da `main`
- [x] `.gitignore` (segredos, PDF, `docs/`, caches)
- [x] `.gitattributes` (LF para `.sh` e `Dockerfile`)
- [x] `.env.example` com todas as variáveis
- [x] `.env` local criado a partir do exemplo
- [ ] **Colar a `OPENROUTER_API_KEY` no `.env`** (usuário)
- [x] `pgadmin/servers.json`
- [x] Skills atualizadas para a estrutura nova
- [ ] Commit (aguardando aprovação)

## Fase 1 — Servidor MCP 🟡

- [x] `schemas/` por assunto: `pricing`, `product`, `tools`, `dummyjson`, `health`, `settings`
- [x] `domain/`: erros e port `ProductCatalog`
- [x] `application/`: `SearchProductsUseCase`, `GetProductDetailUseCase`
- [x] `infrastructure/dummyjson/`: cliente HTTP (timeout + retry com backoff), mapper anticorrupção, catálogo
- [x] `interfaces/mcp/`: `SearchProductsTool`, `ProductDetailTool`, `CatalogErrorTranslator`, `HealthRoute`, `CatalogMcpServerFactory`
- [x] `main.py` (`Application`: composition root, Streamable HTTP stateless, allowlist de hosts)
- [x] Dockerfile multi-stage (`base` / `test` / `runtime`) e `mcp-server/compose.yml`
- [x] 19 testes, ruff e ty verdes via `docker compose --profile test run --rm mcp-server-tests`
- [x] Teste ponta a ponta pelo compose contra a DummyJSON real
- [ ] Commits (aguardando aprovação)

## Fase 2 — Validar o modelo na OpenRouter ⬜

- [ ] Chamada curta com `tools` + `text.format` `json_schema` `strict` no modelo candidato (`openai/gpt-4.1-mini`)
- [ ] Confirmar que o schema do `RequisitionDraft` é aceito (`anyOf` de `X | None`, sem `minimum`)
- [ ] Fixar o modelo no `.env.example`
- [ ] Medir custo e latência de uma execução típica

## Fase 3 — Backend: schemas e domínio ⬜

- [ ] `schemas/pricing/`: `Money`, `Currency`, `Budget`
- [ ] `schemas/product/`: `ProductSnapshot`
- [ ] `schemas/requisition/`: `Requisition` (aggregate root, calcula total), `RequisitionItem`, `RequisitionStatus`
- [ ] `schemas/agent/`: `DraftItem`, `RequisitionDraft`, `ToolCallTrace`, `AgentRun`
- [ ] `schemas/settings/`: `Settings`
- [ ] `domain/errors/`: `DomainError` + um erro por arquivo, com `user_message` em pt-BR
- [ ] `domain/ports/`: `PurchasingAgent`, `CatalogToolsGateway`, `RequisitionRepository`, `UnitOfWork`
- [ ] `domain/services/`: `GroundingValidator`, `RequisitionFactory`
- [ ] Testes de domínio (totais, grounding, orçamento, estoque)

## Fase 4 — Backend: casos de uso ⬜

- [ ] `CreateRequisitionUseCase` (agente → grounding → factory → Unit of Work; idempotency key)
- [ ] `ListRequisitionsUseCase`
- [ ] Fakes: `FakePurchasingAgent`, `InMemoryUnitOfWork`, `InMemoryRequisitionRepository`
- [ ] Testes: criado, nada atende, item não observado, preço do snapshot, idempotência

## Fase 5 — Backend: persistência ⬜

- [ ] `Database`, `RequisitionTable`, `RequisitionItemTable`, `RequisitionTableMapper`
- [ ] `SqlModelRequisitionRepository`, `SqlModelUnitOfWork`
- [ ] Alembic (`migrations/`, `script.py.mako` com `sqlmodel.sql.sqltypes`) e primeira migration revisada
- [ ] `scripts/prestart.sh` com `alembic upgrade head`
- [ ] Testes com SQLite in-memory

## Fase 6 — Backend: agente ⬜

- [ ] `McpToolsGateway` (cliente MCP v2, timeout)
- [ ] `McpToolSchemaConverter`, `ToolCallExecutor`, `OpenAIErrorTranslator`
- [ ] `SystemPrompt` (pt-BR, regra de tradução notebook → laptop)
- [ ] `OpenRouterPurchasingAgent` (loop, limite de iterações, saída estruturada)
- [ ] Testes do conversor e do executor sem rede

## Fase 7 — Backend: HTTP ⬜

- [ ] `schemas/api/`: `CreateRequisitionRequest`, `RequisitionCreatedResponse`, `RequisitionPublic`, `ToolCallPublic`, `ErrorResponse`
- [ ] `RequisitionsRouter` (`POST`/`GET /requisicoes`, header `Idempotency-Key`), `HealthRouter`
- [ ] `DomainErrorHandler` (422/502/503/504), `CorrelationIdMiddleware`
- [ ] Providers em `interfaces/http/dependencies/`
- [ ] `main.py` (`Application`, lifespan com `AsyncOpenAI` e engine)
- [ ] Testes com `TestClient` + `dependency_overrides`

## Fase 8 — Integração com Docker (marco principal) ⬜

- [ ] `backend/Dockerfile` (multi-stage) e `backend/compose.yml` (+ `backend-tests`)
- [ ] `include` do backend no `compose.yml` da raiz
- [ ] `docker compose up --build`: db, pgadmin, mcp-server e backend saudáveis
- [ ] Tabelas visíveis no pgAdmin
- [ ] **Pedido de exemplo funcionando via `POST /requisicoes`**
- [ ] Derrubar o mcp-server e conferir a mensagem 503

## Fase 9 — Chat (Next.js) ⬜

- [ ] Confirmar com o usuário o estilo do frontend (componentes como funções, lógica em classes)
- [ ] Route Handler BFF (`/api/requisicoes`) com timeout
- [ ] Chat com estados: enviando, sucesso (Requisição nº, itens, total), 422 (o que falta), 5xx (`detail`)
- [ ] `ToolCallList` (diferencial)
- [ ] Dockerfile standalone e `frontend/compose.yml`, incluídos na raiz
- [ ] `npm run lint` e `npm run build` verdes

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

- [ ] Decidir: o MCP chama um endpoint interno do backend, ou o MCP grava direto no Postgres
- [ ] Implementar e ajustar o prompt e o grounding

---

## Cronograma sugerido

| Quando | O quê |
|---|---|
| Hoje, até 19h | Aprovar e commitar setup + MCP; validar o modelo; schemas e domínio do backend |
| Hoje, 19h–21h | Casos de uso, persistência e agente |
| Hoje, 21h–23h | HTTP e integração Docker (**pedido de exemplo funcionando**) |
| Amanhã, 8h–11h | Chat Next.js |
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

## Decisões pendentes (consultar o usuário)

- [ ] Quando commitar o que já está pronto (setup, skills, MCP)
- [ ] Formato do dinheiro na API do backend: objeto `Money` ou string
- [ ] Estilo do frontend (classes onde der vs. idioma React)
- [ ] Fazer ou não a terceira tool `criar_requisicao`, e com qual desenho

## Riscos

| Risco | Mitigação |
|---|---|
| Provider da OpenRouter rejeitar o schema `strict` | Validar na Fase 2; simplificar o schema e validar no domínio |
| Chave com orçamento limitado | Modelo barato; evals só quando necessário |
| `docker compose up` falhar na máquina do avaliador | Teste em clone limpo; fail-fast no `.env`; healthchecks |
| Prazo | Marco da Fase 8 hoje; diferenciais só depois do fluxo completo |
| Termos em português sem resultado na DummyJSON (`notebook` = 0) | Regra de tradução no prompt + caso nos evals |
