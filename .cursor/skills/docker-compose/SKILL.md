---
name: docker-compose
description: Ambiente do case com Docker Compose - um compose.yml por serviço (db, pgadmin, mcp-server, backend, frontend) e um compose.yml na raiz com include que sobe tudo com docker compose up; Dockerfiles multi-stage (base/test/runtime) com pip e requirements fixados, testes via profile test, healthchecks, depends_on com service_healthy e .env com fail-fast. Use ao criar ou alterar compose.yml, Dockerfiles, .env.example ou ao depurar o ambiente subindo.
---

# Docker Compose e ambiente

Critério "Funciona" (35%): **"seguindo o README, o projeto sobe na nossa máquina"**. O único pré-requisito no host é o Docker.

## Estrutura: uma responsabilidade por arquivo

```
case/
├── compose.yml              # só include: (sobe tudo)
├── db/compose.yml           # Postgres + volume + healthcheck
├── pgadmin/compose.yml      # pgAdmin + servers.json
├── mcp-server/Dockerfile, compose.yml
├── backend/Dockerfile, compose.yml
└── frontend/Dockerfile, compose.yml
```

Raiz:

```yaml
name: agente-compras

include:
  - path: db/compose.yml
    env_file: .env
  - path: pgadmin/compose.yml
    env_file: .env
  - path: mcp-server/compose.yml
    env_file: .env
  - path: backend/compose.yml
    env_file: .env
  - path: frontend/compose.yml
    env_file: .env
```

- Os caminhos dentro de cada `compose.yml` incluído (`build.context`, volumes) são relativos à pasta do próprio serviço.
- Um serviço pode depender de outro definido em outro arquivo incluído (verificado: `depends_on` atravessa os `include`).
- Cada serviço Python tem também um serviço `<nome>-tests` com `profiles: [test]`. Ele não sobe no `docker compose up`.

## Regras

1. Para rodar: `cp .env.example .env`, preencher `OPENROUTER_API_KEY` e `docker compose up --build`.
2. Variável obrigatória usa **fail-fast**: `${OPENROUTER_API_KEY:?defina OPENROUTER_API_KEY no .env}`.
3. **A ordem de subida é garantida por healthchecks**, não por `sleep`: `db` e `mcp-server` → `backend` (roda a migration e expõe `/health`) → `frontend`. O `pgadmin` só depende do `db`.
4. Containers rodam como usuário não-root, com imagens slim.
5. Os serviços se encontram pelo nome (`http://mcp-server:8000/mcp`, `db:5432`), nunca por `localhost`.
6. O MCP precisa de `allowed_hosts` com `mcp-server` e `mcp-server:*`. Sem isso, o backend recebe 421 (skill `mcp-server`).
7. A porta do Postgres não é exposta no host. Ficam expostos o frontend (3000), o backend (8000, `/docs`) e o pgAdmin (5050).
8. O pgAdmin é ferramenta de inspeção: nenhum serviço depende dele. O servidor `db` já vem registrado via `pgadmin/servers.json`; basta abrir http://localhost:5050 e informar a senha do Postgres.

## Composes por serviço (modelos)

`db/compose.yml`:

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD no .env}
      POSTGRES_DB: ${POSTGRES_DB:-compras}
    volumes:
      - db-data:/var/lib/postgresql            # Postgres 18+: sem /data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
    restart: unless-stopped

volumes:
  db-data:
```

`mcp-server/compose.yml`:

```yaml
services:
  mcp-server:
    build: { context: ., target: runtime }
    environment:
      DUMMYJSON_TIMEOUT_S: ${DUMMYJSON_TIMEOUT_S:-5}
      DUMMYJSON_MAX_ATTEMPTS: ${DUMMYJSON_MAX_ATTEMPTS:-3}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 5s
    restart: unless-stopped

  mcp-server-tests:
    build: { context: ., target: test }
    profiles: [test]
```

`backend/compose.yml`:

```yaml
services:
  backend:
    build: { context: ., target: runtime }
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-app}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-compras}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:?defina OPENROUTER_API_KEY no .env}
      OPENROUTER_MODEL: ${OPENROUTER_MODEL:?defina OPENROUTER_MODEL no .env}
      MCP_URL: http://mcp-server:8000/mcp
      LLM_TIMEOUT_S: ${LLM_TIMEOUT_S:-60}
    depends_on:
      db:
        condition: service_healthy
        restart: true
      mcp-server:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 20
      start_period: 15s
    restart: unless-stopped

  backend-tests:
    build: { context: ., target: test }
    profiles: [test]
```

`frontend/compose.yml`: `ports: ["3000:3000"]`, `BACKEND_URL: http://backend:8000`, `depends_on: backend: condition: service_healthy`.

`pgadmin/compose.yml`: imagem `dpage/pgadmin4:9`, porta `5050:80`, `PGADMIN_CONFIG_SERVER_MODE: "False"`, `PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"`, volume `./servers.json:/pgadmin4/servers.json:ro`, `depends_on: db: condition: service_healthy`. O e-mail padrão precisa de domínio válido (`admin@example.com`; o pgAdmin rejeita `.local`).

## Dependências: pip + requirements fixados

Decisão: pip + `requirements.txt` **totalmente fixado** (inclusive dependências indiretas), em vez de uv. O build é reprodutível e o Dockerfile fica simples; o trade-off é não ter verificação de hashes nem a velocidade do uv.

- `requirements.in`: dependências diretas, sem versão.
- `requirements.txt`: gerado por `pip freeze` dentro de `python:3.14-slim`. É o que a imagem instala.
- `requirements-dev.txt`: `-r requirements.txt` + pytest, ruff, ty e o que eles puxam, fixados.

Gerar/atualizar o lock sem instalar nada no host (rodar na pasta do serviço):

```bash
docker run --rm -v "${PWD}:/w" -w /w python:3.14-slim sh -c \
  "pip install -q -r requirements.in && pip freeze > requirements.txt"
```

## Dockerfile Python (multi-stage: base / test / runtime)

```dockerfile
FROM python:3.14-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY pyproject.toml .
COPY src ./src
COPY tests ./tests
CMD ["sh", "-c", "ruff check . && ruff format --check . && ty check && pytest"]

FROM base AS runtime
COPY src ./src
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["python", "-m", "catalog_mcp.main"]
```

- No backend, o código fica em `app/` (sem `src/`): `PYTHONPATH=/app`, copie `app`, `alembic.ini` e `scripts`, e use `CMD ["sh", "-c", "scripts/prestart.sh && fastapi run app/main.py --port 8000"]`.
- Dependências são instaladas antes de copiar o código, o que preserva o cache de camadas.
- `.dockerignore` em cada serviço: `.venv`, `**/__pycache__`, `.pytest_cache`, `.ruff_cache`, `.env`, `compose.yml` (e `node_modules`, `.next` no frontend).
- O `prestart.sh` precisa de fim de linha LF (o `.gitattributes` já força `*.sh text eol=lf`).

## Comandos

| Objetivo | Comando |
|---|---|
| Subir tudo | `docker compose up --build` |
| Subir um serviço (e dependências) | `docker compose up -d --build --wait mcp-server` |
| Testes + lint de um serviço | `docker compose --profile test run --rm mcp-server-tests` |
| Validar a configuração | `docker compose config -q` |
| Zerar o banco | `docker compose down -v` |

## Depuração rápida

| Sintoma | Causa provável |
|---|---|
| backend `421 Misdirected Request` ao chamar o MCP | falta `allowed_hosts` no `transport_security` do MCP |
| `prestart.sh: not found` / `\r` | o script tem CRLF; confira o `.gitattributes` |
| backend reinicia em loop | `DATABASE_URL` errada ou migration quebrada (`docker compose logs backend`) |
| frontend 502 em toda chamada | `BACKEND_URL` aponta para `localhost`; deveria ser `backend` |
| o Postgres ignora a nova senha | o volume antigo ainda existe; rode `docker compose down -v` |
| variável vazia num compose incluído | falta `env_file: .env` no `include` da raiz |

## Checklist

- [ ] Numa máquina limpa, `docker compose up --build` sobe tudo sem passo manual extra
- [ ] Cada serviço tem seu `Dockerfile` e `compose.yml`; a raiz só faz `include`
- [ ] Todos os serviços têm healthcheck, e o `depends_on` usa `service_healthy`
- [ ] Nenhum segredo está no compose nem nas imagens. Tudo vem do `.env`
- [ ] Testes de cada serviço Python rodam via `--profile test`
