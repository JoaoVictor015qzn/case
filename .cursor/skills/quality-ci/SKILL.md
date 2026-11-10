---
name: quality-ci
description: Qualidade e comunicação do case - pytest (anyio) sem rede e sem chave de LLM, Ruff, ty, ESLint, GitHub Actions com lint e testes, script de avaliação com 5 pedidos que mede acertos do agente, e o modelo de README (como rodar, decisões, uso de IA). Use ao escrever testes, configurar lint/CI, criar ou rodar o script de evals, ou escrever/revisar o README.
---

# Qualidade, CI, evals e README

## Pirâmide de testes

| Nível | Onde | Dublês | Rede/LLM |
|---|---|---|---|
| Domínio (regras, totais, grounding) | `backend/tests/domain/` | nenhum | não |
| Casos de uso | `backend/tests/application/` | `FakePurchasingAgent`, `InMemoryUnitOfWork` | não |
| HTTP | `backend/tests/interfaces/` | `dependency_overrides` | não |
| Infra do backend | `backend/tests/infrastructure/` | SQLite in-memory, fakes do gateway MCP | não |
| Tools MCP (**requisito**) | `mcp-server/tests/interfaces/test_*_tool.py` | `FakeProductCatalog` + `Client(server)` | não |
| Adapter DummyJSON | `mcp-server/tests/infrastructure/` | `ScriptedTransport` (`httpx.MockTransport`) | não |
| Evals do agente | `backend/evals/` | nenhum (sistema real) | **sim**, manual |

- O `pytest` roda **sem** `OPENROUTER_API_KEY` e sem internet. Isso é requisito do case para as tools MCP e vale para todo o resto.
- Dublês e dados de exemplo ficam em `tests/fakes/`, **uma classe por arquivo** (`FakeProductCatalog`, `SampleProducts`, `ScriptedTransport`). Os testes em si são funções `test_*` do pytest, agrupados por arquivo segundo a classe testada.
- Testes async usam `@pytest.mark.anyio` com a fixture `anyio_backend` retornando `"asyncio"`, como faz a doc oficial do MCP.
- Nomeie os testes pelo comportamento: `test_buscar_produtos_returns_empty_list_when_no_match`.
- Use Arrange / Act / Assert e **um** comportamento por teste.

## Lint e tipos (Python)

```toml
[tool.ruff]
target-version = "py314"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG001", "T201", "FAST"]
ignore = ["E501", "B008", "B904"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]        # backend: ["."]

[tool.ty.environment]
root = ["./src", "."]            # backend: ["."]

[tool.ty.terminal]
error-on-warning = true
```

A base é a configuração do full-stack-fastapi-template. Adicionamos `FAST`, porque a skill oficial do FastAPI diz "Consider enabling the FastAPI rules".

Comandos (sem nada instalado no host): o estágio `test` do Dockerfile roda ruff, ty e pytest.

```bash
docker compose --profile test run --rm mcp-server-tests
docker compose --profile test run --rm backend-tests
```

Para **aplicar** a formatação (o container de teste trabalha numa cópia do código), rode na pasta do serviço:

```bash
docker run --rm -v "${PWD}:/w" -w /w python:3.14-slim sh -c \
  "pip install -q -r requirements-dev.txt && ruff format . && ruff check --fix ."
```

## CI (`.github/workflows/ci.yml`)

```yaml
name: ci
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [mcp-server, backend]
    steps:
      - uses: actions/checkout@v4
      - run: cp .env.example .env
      - run: docker compose --profile test run --rm ${{ matrix.service }}-tests
        env: { OPENROUTER_API_KEY: dummy, OPENROUTER_MODEL: dummy, POSTGRES_PASSWORD: dummy }
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 24, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
      - run: npm run lint
      - run: npm run build
  compose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cp .env.example .env
      - run: docker compose config -q
        env: { OPENROUTER_API_KEY: dummy, OPENROUTER_MODEL: dummy, POSTGRES_PASSWORD: dummy }
```

O CI roda os mesmos containers de teste que rodam localmente: o que passa na máquina passa no CI. Use a versão mais recente de cada action no momento de criar o workflow.

## Script de evals (diferencial: "5 pedidos, quantos acertou")

`backend/evals/` roda contra o sistema no ar (`http://localhost:8000`), em classes como o resto do código:

```
backend/evals/
├── run_evals.py          # EvalRunner: executa os casos, imprime tabela, exit code ≠ 0 abaixo do mínimo
├── eval_case.py          # EvalCase (Pydantic): pedido + expectativas
├── eval_result.py        # EvalResult (Pydantic): acertou?, motivos da falha
├── eval_checker.py       # EvalChecker: aplica as regras de acerto
└── eval_cases.py         # EvalCases.ALL: os 5 casos
```

```python
ALL = [
    EvalCase(request_text="Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada.",
             expect_status=201, category="laptops", quantity=3, max_unit_price=Decimal("2000")),
    EvalCase(request_text="Preciso de 2 notebooks de até US$ 1.500 cada.",     # testa a tradução notebook -> laptop
             expect_status=201, category="laptops", quantity=2, max_unit_price=Decimal("1500")),
    EvalCase(request_text="Quero 2 smartphones de até US$ 1.000 cada.",
             expect_status=201, category="smartphones", quantity=2, max_unit_price=Decimal("1000")),
    EvalCase(request_text="Preciso de 5 Ferraris até US$ 10 cada.",
             expect_status=422),                      # não existe: não pode inventar
    EvalCase(request_text="Quero 3 laptops por no máximo US$ 50 cada.",
             expect_status=422),                      # existe, mas fora do orçamento
]
```

Rodar com o ambiente no ar: `docker compose run --rm backend-tests python -m evals.run_evals` (apontando `EVALS_BASE_URL=http://backend:8000`).

Um caso conta como acerto quando:
- o status HTTP é o esperado;
- todos os itens são da categoria esperada;
- a soma das quantidades bate com o pedido;
- todo `unit_price` respeita o orçamento;
- `total == Σ line_total`.

Saída esperada: `4/5 acertos (80%)`, com o motivo de cada falha. **Antes de fixar os cenários, confira as expectativas contra o catálogo real da DummyJSON.**

## README (comunicação: 15%)

O case pede um README "em poucas linhas". Use estas seções, nesta ordem:

```markdown
# Agente de compras

## Como rodar
1. `cp .env.example .env` e preencha `OPENROUTER_API_KEY` (e `OPENROUTER_MODEL`).
2. `docker compose up --build`
3. Abra http://localhost:3000 e envie: "Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada."

## Arquitetura
(diagrama das 4 peças + pgAdmin, 1 parágrafo sobre DDD: contextos Catálogo e Compras, schemas por assunto)

## Principais decisões
- Loop de agente próprio (sem framework): o modelo decide as tools; ...
- Grounding: preço e produto vêm só do retorno das tools; total calculado no backend com Decimal.
- Erros externos → mensagens claras (DummyJSON fora = 503, timeout = 504).
- Migrations com Alembic no start; Postgres 18; ...

## Testes
`docker compose --profile test run --rm mcp-server-tests` e `backend-tests` (sem chave de LLM) · evals com o ambiente no ar

## Uso de IA
Como a IA foi usada (ferramentas, para quê, o que foi revisado/decidido manualmente).

## Limitações e próximos passos
```

Cada decisão segue o formato **o quê**, depois **por quê**, depois **trade-off**, em uma linha. Isso prepara a conversa com os avaliadores.

## Checklist antes de entregar

- [ ] `pytest` passa nos dois serviços Python sem chave e sem rede
- [ ] Ruff, ty, ESLint e o build do Next estão verdes, e o CI passa
- [ ] Os evals rodaram e o resultado está no README
- [ ] Clone limpo, `.env` copiado e `docker compose up --build`: o pedido de exemplo funciona
- [ ] O README tem a seção "Uso de IA"
- [ ] O `.zip` inclui a pasta `.git`, e nenhum segredo aparece no histórico (`git log -p | rg sk-or-`)
