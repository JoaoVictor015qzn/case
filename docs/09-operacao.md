# Operação, testes e qualidade

## Subir o ambiente

```bash
cp .env.example .env        # preencha OPENROUTER_API_KEY e INTERNAL_API_TOKEN
docker compose up --build
```

O `.env` precisa ficar na raiz do projeto, ao lado do `compose.yml`.

## Variáveis de ambiente (`.env`)

| Variável | Obrigatória | Padrão | Uso |
|---|---|---|---|
| `OPENROUTER_API_KEY` | sim | | Chave da OpenRouter |
| `OPENROUTER_MODEL` | sim | `openai/gpt-4.1-mini` | Modelo com tools + saída estruturada |
| `INTERNAL_API_TOKEN` | sim (mín. 16) | | Segredo entre `mcp-server` e `backend` |
| `POSTGRES_PASSWORD` | sim | | Senha do Postgres |
| `POSTGRES_USER` / `POSTGRES_DB` | não | `app` / `compras` | Usuário e banco |
| `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` | não | `admin@example.com` / `admin` | Login do pgAdmin |
| `DUMMYJSON_TIMEOUT_S` / `DUMMYJSON_MAX_ATTEMPTS` | não | 5 / 3 | Timeout e tentativas na DummyJSON |
| `LLM_TIMEOUT_S` | não | 60 | Timeout de cada chamada ao modelo |
| `BACKEND_TIMEOUT_MS` | não | 120000 | Timeout do BFF do chat |

As obrigatórias usam `${VAR:?mensagem}` no compose: sem elas, o `docker compose up` para com uma mensagem clara. Os serviços também validam a configuração no start (`pydantic-settings`).

## Testes

Rodam dentro do estágio `test` de cada Dockerfile (Ruff, formatação, ty e pytest), sem nada instalado no host, **sem chave de LLM e sem internet**.

```bash
docker compose --profile test run --rm --build mcp-server-tests
docker compose --profile test run --rm --build backend-tests
```

| Serviço | Testes | O que cobrem |
|---|---|---|
| `mcp-server` | 34 | Um arquivo por tool (cliente MCP em memória + catálogo falso), busca por categoria, schemas das tools, adapters HTTP (retry, timeout, 404, payload inesperado) |
| `backend` | 85 | Domínio (grounding, agregado, dinheiro), casos de uso, loop do agente com OpenRouter simulada, executor de tools, conversor de schema, repositório em SQLite, rotas HTTP, endpoint interno e o checker dos evals |

Frontend: `npm run lint` e `npm run build` em `frontend/`.

## CI

`.github/workflows/ci.yml`, em todo push e pull request:

| Job | O que roda |
|---|---|
| `python` (matriz `mcp-server`, `backend`) | O mesmo container `*-tests` usado localmente |
| `frontend` | `npm ci`, `npm run lint`, `npm run build` |
| `compose` | `docker compose config -q` (valida todos os compose) |

As variáveis obrigatórias recebem valores fictícios no CI.

## Evals (agente real)

Com o ambiente no ar e uma chave válida:

```bash
docker compose --profile test run --rm -e EVALS_BASE_URL=http://backend:8000 backend-tests python -m evals.run_evals
```

Cinco pedidos (`backend/evals/eval_cases.py`): 3 laptops até US$ 2.000, "notebook" → laptop, 2 smartphones até US$ 1.000, Ferrari (deve dar 422) e laptops até US$ 50 (deve dar 422).

Um caso só conta como acerto se:

- o status HTTP é o esperado;
- título e preço de cada item batem com a DummyJSON (consultada direto, sem passar pelo MCP);
- a categoria de cada item é a esperada;
- a soma das quantidades e o orçamento batem com o pedido;
- o total é a soma dos subtotais;
- a requisição passou por `criar_requisicao`.

Imprime `N/5 acertos` com o motivo de cada falha e sai com código 1 abaixo de `EVALS_MIN_PASSED` (padrão 4).

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `GetFileAttributesEx ... .env: The system cannot find the file` | `.env` ausente na raiz | `cp .env.example .env` na pasta do `compose.yml` |
| `defina X no .env` | Variável obrigatória vazia | Preencha no `.env` |
| `Bind for 0.0.0.0:8000 failed: port is already allocated` | Outra aplicação na porta (8000, 3000 ou 5050) | Pare a aplicação ou troque o lado esquerdo de `ports` no compose do serviço |
| Backend reiniciando com `failed to resolve host 'db'` | Container criado com rede quebrada após falha anterior | `docker compose down` e `docker compose up -d` |
| Chat responde "O acesso ao modelo de linguagem foi recusado" (502) | Chave inválida, sem crédito ou modelo indisponível | Confira a chave em `https://openrouter.ai/api/v1/key`; depois `docker compose up -d --force-recreate backend` |
| 503 "catálogo indisponível" | DummyJSON ou MCP fora | `docker compose ps`; teste `https://dummyjson.com/products/1` |
| Mudou o `.env` e nada mudou | O container lê o `.env` só ao ser criado | `docker compose up -d --force-recreate <serviço>` |

Logs: `docker compose logs -f backend mcp-server`. Cada linha do backend traz o correlation id, também devolvido no header `X-Request-ID`.
