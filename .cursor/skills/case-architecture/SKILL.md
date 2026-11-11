---
name: case-architecture
description: Arquitetura, requisitos e padrões do case "agente de compras" (Forward Deployed Engineer). Define DDD tático, estrutura de pastas com schemas/ por assunto, uma classe Pydantic por arquivo, regras de Clean Code, padrões de system design, containers por serviço, glossário e definição de pronto. Use em qualquer tarefa deste repositório, ao criar módulos, decidir onde um código mora, revisar código ou escrever o README.
---

# Case: agente de compras — arquitetura e padrões

Fonte da verdade do escopo: [requirements.md](requirements.md), que transcreve o PDF do case (em `docs/`, fora do git porque contém a chave da OpenRouter). O andamento fica em `ROADMAP.md` na raiz.

## Regra de trabalho com o usuário

**Nada de decisão unilateral.** Não commitar, não fazer push, não apagar arquivos e não mudar estrutura, stack ou convenção sem perguntar antes. Na dúvida, proponha e espere a aprovação.

## O sistema em uma frase

A pessoa digita um pedido no chat (Next.js) → o backend (FastAPI) roda um agente (LLM via OpenRouter) que decide sozinho quando chamar as ferramentas do servidor MCP (que consulta a DummyJSON) → o backend valida o resultado, salva a requisição no Postgres e devolve itens, quantidades, preços e total.

```
[frontend: Next.js] --HTTP--> [backend: FastAPI + agente] --MCP Streamable HTTP--> [mcp-server] --HTTPS--> DummyJSON
                                      |
                                      +--SQL--> [db: Postgres] <-- [pgadmin]    +--HTTPS--> OpenRouter (LLM)
```

## Stack (fixa)

| Peça | Stack | Skill |
|---|---|---|
| Servidor MCP | Python 3.14, `mcp` v2 (`MCPServer`), httpx, pip + `requirements.txt` fixado | `mcp-server` |
| Backend | FastAPI, SDK `openai` → OpenRouter (Responses API), cliente `mcp` | `fastapi-backend`, `agent-loop` |
| Banco | Postgres 18, SQLModel + Alembic + psycopg 3, pgAdmin para inspeção | `database-sqlmodel` |
| Chat | Next.js (App Router, TypeScript), `output: "standalone"` | `nextjs-chat` |
| Ambiente | Docker Compose com um `compose.yml` por serviço + `include` na raiz | `docker-compose` |
| Qualidade | pytest, Ruff, ty, GitHub Actions, script de avaliação | `quality-ci` |

Todo o código (classes, métodos, variáveis, arquivos) é em **inglês**. Em português ficam só os nomes que o case fixa (`buscar_produtos`, `detalhar_produto`, `criar_requisicao`, `/requisicoes`) e os textos para o usuário final e para o LLM (mensagens de erro, docstrings das tools, prompt).

## DDD tático

Dois **bounded contexts**, cada um no seu serviço:

| Contexto | Serviço | Linguagem |
|---|---|---|
| Catálogo | `mcp-server` | Product, Money, busca, detalhe |
| Compras | `backend` | Requisition, RequisitionItem, Budget, grounding |

Blocos de construção:
- **Aggregate root**: `Requisition`. Os itens só existem dentro dela, e ela calcula o próprio total. Nunca se grava um `RequisitionItem` sozinho.
- **Value objects**: `Money`, `Currency`, `Budget`, `ProductSnapshot`. Imutáveis (`frozen=True`), comparados por valor.
- **Domain services**: regras que não pertencem a uma entidade só, como `GroundingValidator` (anti-invenção).
- **Factory**: `RequisitionFactory` monta o agregado a partir do rascunho validado.
- **Repository**: um por agregado (`RequisitionRepository`), definido como port no domínio.
- **Anti-corruption layer**: o formato externo (DummyJSON, OpenRouter, MCP) é traduzido por mappers na infraestrutura e não vaza para dentro.

## Estrutura de pastas

```
case/
├── compose.yml                      # include: de todos os serviços; "docker compose up" sobe tudo
├── .env.example                     # versionado; .env NUNCA
├── README.md, ROADMAP.md
├── db/compose.yml                   # Postgres
├── pgadmin/compose.yml, servers.json
├── mcp-server/
│   ├── Dockerfile                   # estágios base / test / runtime
│   ├── compose.yml                  # mcp-server + mcp-server-tests (profile test)
│   ├── pyproject.toml               # só config de ferramentas (ruff, pytest, ty)
│   ├── requirements.in / requirements.txt / requirements-dev.txt
│   ├── src/catalog_mcp/             # ver skill mcp-server
│   └── tests/                       # fakes/, interfaces/, infrastructure/
├── backend/
│   ├── Dockerfile, compose.yml, pyproject.toml, requirements*.txt, alembic.ini
│   ├── scripts/prestart.sh          # alembic upgrade head
│   ├── evals/                       # script com 5 pedidos de teste
│   ├── tests/                       # fakes/, domain/, application/, interfaces/, infrastructure/
│   └── app/
│       ├── main.py                  # Application: composition root (FastAPI, lifespan, handlers)
│       ├── schemas/                 # TODAS as classes Pydantic, uma pasta por assunto
│       │   ├── pricing/             # Money, Currency, Budget
│       │   ├── product/             # ProductSnapshot
│       │   ├── requisition/         # Requisition, RequisitionItem, RequisitionStatus
│       │   ├── agent/               # RequisitionDraft, DraftItem, AgentRun, ToolCallTrace
│       │   ├── api/                 # CreateRequisitionRequest, RequisitionCreatedResponse, RequisitionPublic, ErrorResponse
│       │   ├── health/              # HealthStatus
│       │   └── settings/            # Settings
│       ├── domain/
│       │   ├── errors/              # DomainError + uma classe por erro
│       │   ├── ports/               # RequisitionRepository, UnitOfWork, PurchasingAgent (ABC)
│       │   └── services/            # GroundingValidator, RequisitionFactory
│       ├── application/             # CreateRequisitionUseCase, ListRequisitionsUseCase
│       ├── infrastructure/
│       │   ├── llm/                 # OpenRouterPurchasingAgent, SystemPrompt, McpToolSchemaConverter
│       │   ├── mcp/                 # McpToolsGateway
│       │   └── persistence/         # Database, tables/, mappers/, SqlModelRequisitionRepository, SqlModelUnitOfWork, migrations/
│       └── interfaces/http/
│           ├── routes/              # RequisitionsRouter, HealthRouter
│           ├── errors/              # DomainErrorHandler (domínio → HTTP)
│           ├── middleware/          # CorrelationIdMiddleware
│           └── dependencies/        # providers do FastAPI (Annotated + Depends)
└── frontend/
    ├── Dockerfile, compose.yml, next.config.ts, package.json
    └── src/                         # ver skill nextjs-chat
```

## Regra de dependência

Dependências apontam **para dentro**:

```
interfaces / infrastructure  ──►  application  ──►  domain  ──►  schemas (dados)
(FastAPI, MCP, SQLModel,          (casos de uso)     (regras,      (classes Pydantic
 OpenAI, httpx)                                       ports, erros)  por assunto)
```

- `schemas/` não importa nada das outras camadas, só Pydantic e outros schemas.
- `domain/` e `application/` não importam FastAPI, SQLModel, httpx, openai nem mcp. Também não usam `schemas/api/` (DTO HTTP é assunto da interface).
- `infrastructure/` implementa os ports. É o único lugar que fala com OpenRouter, MCP, DummyJSON e Postgres.
- `interfaces/` traduz o protocolo (HTTP ou MCP) ↔ caso de uso.
- A composição (qual implementação entra em cada port) acontece **só** no composition root: `main.py` (`Application`) e, no backend, `interfaces/http/dependencies/`.

## Clean Code: regras do projeto

- **Uma classe por arquivo.** O arquivo tem o nome da classe em snake_case (`SearchProductsTool` → `search_products_tool.py`).
- **Todo dado é uma classe Pydantic** (`BaseModel`), em `schemas/<assunto>/`. Entidades e value objects usam `ConfigDict(frozen=True)`. **Não use `dataclass`, `TypedDict`, `NamedTuple` nem `dict` solto** atravessando camadas.
- **Comportamento mora em classes**, com dependências injetadas pelo construtor. Não há funções soltas em módulo nem funções aninhadas (por exemplo, tools definidas dentro de uma factory). Exceções aceitas: funções de teste e fixtures do pytest, e aliases `Annotated` (como `SearchTerm`).
- **Ports são `ABC`** com `@abstractmethod`, em `domain/ports/`. Implementações herdam explicitamente.
- **Exceções são classes** em `domain/errors/`, uma por arquivo, todas herdando de um erro base do contexto (`CatalogError`, `DomainError`). Nunca `except Exception: pass`. O mapeamento para o protocolo (HTTP ou `ToolError`) acontece em um só lugar.
- **Métodos pequenos**, com uma responsabilidade e nome de verbo. Mais de cerca de 30 linhas é sinal para extrair.
- **Sem números mágicos**: timeouts, limites, retentativas e o modelo ficam em `Settings`. Constantes da classe (nome da tool, path da rota) ficam como atributos de classe.
- **Dinheiro é sempre `Decimal`** dentro de `Money`, nunca `float`. No banco, `NUMERIC(12,2)`. Moeda USD.
- **Tipagem completa**, `ty` sem erros nem warnings, sem `Any` sem justificativa.
- **Sem comentários óbvios.** Docstring só onde vira contrato (tools MCP, ports) ou explica restrição.
- **Sem `print`.** Use `logging` com contexto (correlation id, tool, duração).

## System design: padrões aplicados

Cada padrão resolve um problema concreto do case e vira uma linha no README.

| Padrão | Onde | Problema que resolve |
|---|---|---|
| Ports & Adapters | `domain/ports` + `infrastructure` | Trocar LLM, MCP, DummyJSON e banco por fakes nos testes |
| Repository + Unit of Work | `persistence/` | Requisição e itens gravados juntos, ou nada |
| Aggregate, Value Object, Factory | `schemas/requisition`, `domain/services` | Total calculado no domínio, nunca vindo do LLM |
| Anti-Corruption Layer | mappers em `infrastructure` | Formato da DummyJSON e da OpenRouter não vaza para dentro |
| Composition Root / DI | `main.py`, `dependencies/` | Um só lugar decide as implementações |
| Timeout, retry com backoff, fail-fast | clientes HTTP, `Settings`, compose | DummyJSON lenta, OpenRouter instável, `.env` incompleto |
| Idempotency key no `POST` | header `Idempotency-Key` + coluna única | Clique duplo não cria duas requisições |
| Health check + `depends_on: service_healthy` | todos os serviços | Ordem de subida garantida sem `sleep` |
| Correlation id nos logs | middleware HTTP | Rastrear um pedido do chat até a tool chamada |
| Stateless + 12-factor | backend e MCP | Estado só no Postgres, config só por env |

**Fora de escopo** (decidido): CQRS completo, event sourcing, fila de mensagens, saga e cache distribuído. Adicionariam peças sem resolver problema do case.

## System design: decisões obrigatórias

1. **O modelo decide as tools.** Não há fluxo fixo do tipo "sempre buscar e depois detalhar". O loop só executa o que o modelo pede (skill `agent-loop`).
2. **Sem invenção (grounding).** Todo item da requisição precisa ter `product_id` retornado por uma tool **nesta execução**. Preço e título vêm do snapshot da tool, **nunca do texto do LLM**. O total é calculado no domínio com `Decimal`.
3. **Pedido impossível**: o sistema não salva nada e responde com `missing`, a lista do que falta.
4. **Timeouts em toda I/O de rede**: DummyJSON, MCP e OpenRouter, todos configuráveis por env.
5. **Falha externa vira mensagem clara**: DummyJSON fora → `ToolError` → o agente informa, ou 503; timeout → 504; OpenRouter → 502. O chat mostra o `detail`.
6. **Config 12-factor**: tudo por variável de ambiente. Segredos só no `.env` (no `.gitignore`).
7. **Migrations versionadas** com Alembic, rodando a cada start do backend (`prestart.sh`).
8. **Healthchecks** em todos os serviços.
9. **Stateless**: backend e MCP não guardam estado em memória entre requests.

## Glossário

| Termo do case (PT) | No código (EN) |
|---|---|
| requisição de compra | `Requisition` |
| item da requisição | `RequisitionItem` |
| pedido (texto do usuário) | `request_text` |
| produto | `Product` (catálogo) / `ProductSnapshot` (compras) |
| preço / valor | `Money` |
| orçamento por unidade | `Budget` |
| buscar_produtos / detalhar_produto | tools MCP (mantêm o nome em PT) |
| o que falta | `missing` |

## Commits (só quando o usuário autorizar)

Conventional Commits, em português, pequenos e frequentes, na branch `develop`:

```
feat(mcp): adiciona tool buscar_produtos com timeout
test(mcp): cobre detalhar_produto com produto inexistente
fix(backend): retorna 504 quando o MCP excede o timeout
docs: explica decisões de grounding no README
```

## Definição de pronto (para cada peça)

- [ ] Segue a skill da peça, a regra de dependência e as regras de Clean Code acima
- [ ] Uma classe por arquivo, dados em `schemas/<assunto>/`, sem dataclass nem função solta
- [ ] Os testes passam sem rede e sem chave de LLM (`docker compose --profile test run --rm <serviço>-tests`)
- [ ] Ruff (check e format) e ty passam sem erros
- [ ] Os erros externos têm tratamento e mensagem clara
- [ ] O `ROADMAP.md` e, se preciso, o README foram atualizados
