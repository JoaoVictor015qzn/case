---
name: fastapi-backend
description: Padrões do backend FastAPI do case (POST/GET /requisicoes) seguindo a skill oficial do FastAPI, com DDD e classes - routers em classes, providers Annotated + Depends em interfaces/http/dependencies, Settings em schemas/settings, DTOs em schemas/api, Application como composition root com lifespan, DomainErrorHandler central, Idempotency-Key, correlation id, async vs sync com Asyncer e testes com dependency_overrides. Use ao criar ou alterar endpoints, dependências, configuração, tratamento de erros ou testes do backend.
---

# Backend FastAPI (contexto Compras)

Exemplos oficiais (docs do FastAPI e skill oficial): [reference.md](reference.md).
Regras gerais: `case-architecture`. Agente: `agent-loop`. Banco: `database-sqlmodel`.

## Contrato HTTP (fixado pelo case)

| Método | Rota | Sucesso | Erros |
|---|---|---|---|
| `POST` | `/requisicoes` | `201` + `RequisitionCreatedResponse` | `422` (nada atende, com `missing`), `502`, `503`, `504` |
| `GET` | `/requisicoes` | `200` + `list[RequisitionPublic]` | — |
| `GET` | `/health` | `200` + `HealthStatus` | — |

`POST /requisicoes` aceita o header opcional `Idempotency-Key`. Se a mesma chave chegar de novo, devolve a requisição já criada (200) em vez de rodar o agente outra vez.

DTOs em `schemas/api/`, uma classe por arquivo:

```python
class CreateRequisitionRequest(BaseModel):
    request_text: str = Field(min_length=3, max_length=1000)

class RequisitionCreatedResponse(BaseModel):
    requisition: RequisitionPublic   # id (número da requisição), status, items, total, currency, created_at
    message: str                     # resposta do agente em pt-BR
    missing: list[str]
    tool_calls: list[ToolCallPublic] # diferencial: ferramentas no chat

class ErrorResponse(BaseModel):
    detail: str                      # mensagem clara em pt-BR, o chat exibe como está
    missing: list[str] = []
    tool_calls: list[ToolCallPublic] = []
```

Cada DTO tem um `@classmethod from_domain(...)` que converte a partir de `schemas/requisition` ou `schemas/agent`. **Nunca** retorne a tabela SQLModel nem o agregado direto.

## Camadas (onde cada coisa mora)

| Pasta | Classes |
|---|---|
| `interfaces/http/routes/` | `RequisitionsRouter`, `HealthRouter`: cada um expõe `.router` (`APIRouter`) e só chama o caso de uso |
| `interfaces/http/dependencies/` | providers com `Annotated` aliases (`SettingsDep`, `SessionDep`, `CreateRequisitionDep`) |
| `interfaces/http/errors/` | `DomainErrorHandler`: um único ponto de tradução domínio → HTTP |
| `interfaces/http/middleware/` | `CorrelationIdMiddleware`: lê/gera `X-Request-ID` e põe no contexto de log |
| `application/` | `CreateRequisitionUseCase`, `ListRequisitionsUseCase` |
| `schemas/settings/` | `Settings` |
| `main.py` | `Application`: cria o `FastAPI(lifespan=...)`, registra routers, middleware e handlers |

Router em classe:

```python
class RequisitionsRouter:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/requisicoes", tags=["requisicoes"])
        self.router.add_api_route("", self.create, methods=["POST"], status_code=201,
                                  responses={422: {"model": ErrorResponse}, 502: {...}, 503: {...}, 504: {...}})
        self.router.add_api_route("", self.list, methods=["GET"])

    async def create(self, body: CreateRequisitionRequest, use_case: CreateRequisitionDep,
                     idempotency_key: IdempotencyKeyHeader = None) -> RequisitionCreatedResponse:
        result = await use_case.execute(body.request_text, idempotency_key)
        return RequisitionCreatedResponse.from_domain(result)

    def list(self, use_case: ListRequisitionsDep) -> list[RequisitionPublic]:
        return [RequisitionPublic.from_domain(r) for r in use_case.execute()]
```

## Regras da skill oficial do FastAPI (obrigatórias)

1. **`Annotated` sempre**, com type alias para dependências reutilizadas:
   ```python
   SettingsDep = Annotated[Settings, Depends(SettingsProvider.get)]
   SessionDep = Annotated[Session, Depends(DatabaseProvider.session)]
   CreateRequisitionDep = Annotated[CreateRequisitionUseCase, Depends(UseCaseProvider.create_requisition)]
   ```
   Os providers são classes com `@staticmethod` (FastAPI aceita qualquer callable em `Depends`).
2. **Return type** em toda path operation.
3. **Prefix e tags no `APIRouter`**, não no `include_router`.
4. **Uma operação HTTP por método.**
5. Não use `...` como default, não use `RootModel` e não use `ORJSONResponse`/`UJSONResponse`.
6. **async vs sync**:
   - `create` é `async def`, porque o agente e o MCP são async.
   - A persistência com SQLModel é síncrona. Dentro do async, use `await asyncify(uow.commit_requisition)(requisition)` (**Asyncer**).
   - `list` é `def` comum, que roda no threadpool.
   - Nunca rode código bloqueante direto dentro de `async def`.
7. **Lifespan** em vez de `on_event`. Use-o para recursos de vida longa (o `AsyncOpenAI` e o engine), guardados em `app.state`.
8. **Settings via provider com `@lru_cache`**, trocáveis nos testes com `dependency_overrides`.
9. Rode com `fastapi run app/main.py --port 8000`.

## Settings (`schemas/settings/settings.py`)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore", frozen=True)

    database_url: PostgresDsn
    openrouter_api_key: SecretStr
    openrouter_model: str
    openrouter_base_url: HttpUrl = HttpUrl("https://openrouter.ai/api/v1")
    mcp_url: HttpUrl = HttpUrl("http://mcp-server:8000/mcp")
    mcp_timeout_s: float = 30.0
    llm_timeout_s: float = 60.0
    agent_max_iterations: int = Field(default=8, ge=1, le=20)
```

- Segredos usam `SecretStr` e nunca aparecem em log ou em resposta.
- A URL do banco é normalizada para `postgresql+psycopg://` (validator na própria classe).
- O `mcp_timeout_s` precisa cobrir o pior caso do MCP (timeout × tentativas da DummyJSON).

## Erros: `DomainErrorHandler`

```python
class DomainErrorHandler:
    STATUS_BY_ERROR: ClassVar[dict[type[DomainError], int]] = {
        RequisitionNotFulfillableError: 422,
        ToolsUnavailableError: 503,
        CatalogUnavailableError: 503,
        LLMTimeoutError: 504,
        LLMUnavailableError: 502,
        LLMConfigurationError: 502,
        AgentOutputError: 502,
        AgentIterationLimitError: 502,
    }

    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(DomainError, self.handle)

    async def handle(self, request: Request, exc: DomainError) -> JSONResponse:
        status = self.STATUS_BY_ERROR.get(type(exc), 500)
        logger.warning("domain_error error=%s status=%d", type(exc).__name__, status)
        return JSONResponse(status_code=status, content=ErrorResponse.from_error(exc).model_dump())
```

- Cada `DomainError` tem `user_message` em pt-BR, pensado para o usuário final. Ex.: "O catálogo de produtos está indisponível no momento. Tente novamente em instantes."
- Um 500 inesperado **não** vaza o stack para o cliente. O stack vai para o log.

## Testes

```
tests/
├── fakes/            # FakePurchasingAgent, InMemoryRequisitionRepository, InMemoryUnitOfWork, SampleSnapshots
├── domain/           # GroundingValidator, Requisition (totais), Money, Budget
├── application/      # CreateRequisitionUseCase, ListRequisitionsUseCase
├── interfaces/       # rotas com TestClient + dependency_overrides
└── infrastructure/   # repositório (SQLite in-memory), conversor de tools, executor de tool calls
```

- `app.dependency_overrides[UseCaseProvider.create_requisition] = lambda: CreateRequisitionUseCase(FakePurchasingAgent(...), ...)`.
- Sem rede e sem chave de LLM. Rodar: `docker compose --profile test run --rm backend-tests`.
- Cenários mínimos: criado (201); nada atende (422 com `missing`); item não observado é descartado; preço vem do snapshot e não do LLM; MCP fora (503); timeout do LLM (504); mesma `Idempotency-Key` não duplica; `GET` em ordem decrescente de criação.

## Checklist

- [ ] Rotas em classes, sem lógica de negócio, só chamam o caso de uso
- [ ] Toda dependência usa um alias `Annotated`, e a composição fica só em `dependencies/` e `main.py`
- [ ] Toda rota tem return type; DTOs vêm de `schemas/api/`
- [ ] Os erros de domínio são mapeados só no `DomainErrorHandler`, com mensagem clara
- [ ] Não há I/O bloqueante dentro de `async def`
- [ ] Existe o `/health` para o healthcheck do compose
