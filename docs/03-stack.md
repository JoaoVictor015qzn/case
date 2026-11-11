# Stack

Versões fixadas em `requirements.txt` (Python, via pip) e `package-lock.json` (Node).

## Python (mcp-server e backend)

| Tecnologia | Versão | Uso | Por quê |
|---|---|---|---|
| Python | 3.14 | Linguagem dos dois serviços | Uma só stack para MCP e backend; SDK MCP oficial em Python |
| MCP Python SDK (`mcp`) | 2.3.0 | Servidor (`MCPServer`) e cliente das tools | SDK oficial; Streamable HTTP stateless e cliente em memória nos testes |
| Pydantic / pydantic-settings | 2.14 | Todos os dados, DTOs e configuração | Validação e serialização uniformes; fail-fast no start |
| httpx | 0.28 | Chamadas à DummyJSON e ao backend (no MCP) | Async, timeouts e `MockTransport` para testes sem rede |
| FastAPI | 0.162 | API HTTP do backend | Tipos Pydantic nativos, `Depends`, OpenAPI automático |
| openai (SDK) | 3.49 | Cliente da OpenRouter (Responses API) | A OpenRouter é compatível com o SDK; retries e timeout prontos |
| SQLModel / SQLAlchemy | 0.0.48 / 2.1 | Tabelas e consultas | Mesmos tipos do FastAPI/Pydantic |
| Alembic | 1.20 | Migrations versionadas | Tabelas criadas automaticamente no start do backend |
| psycopg | 3.3 | Driver do Postgres | Driver moderno, binário incluído |
| asyncer | 0.0.18 | `asyncify` para rodar a persistência síncrona sem travar o loop | Recomendado pela skill oficial do FastAPI |
| pytest + anyio | 9.2 | Testes async | Padrão dos exemplos oficiais do MCP |
| Ruff | 0.17 | Lint e formatação | Rápido; regras do full-stack-fastapi-template + `FAST` |
| ty | 0.0.100 | Checagem de tipos | `error-on-warning` ligado |

## Frontend

| Tecnologia | Versão | Uso | Por quê |
|---|---|---|---|
| Next.js (App Router) | 16.4.6 | Chat e BFF (Route Handler) | BFF no mesmo projeto; build `standalone` pequeno para Docker |
| React | 19.3 | Componentes do chat | Padrão do Next |
| TypeScript | 5 | Tipagem | Tipos espelhando a API em `lib/types/` |
| ESLint | 9 | Lint | Configuração do `create-next-app` |

## Infraestrutura

| Tecnologia | Versão | Uso |
|---|---|---|
| Docker Compose | `include` (Compose v2.20+) | Um compose por serviço + raiz que sobe tudo |
| Postgres | 18 | Banco das requisições |
| pgAdmin | 9 | Inspeção do banco, com servidor pré-cadastrado em `pgadmin/servers.json` |
| Node | 24-slim | Imagem do frontend |
| python | 3.14-slim | Imagem dos serviços Python |
| GitHub Actions | `checkout@v6`, `setup-node@v6` | CI |

## Serviços externos

| Serviço | Uso |
|---|---|
| [OpenRouter](https://openrouter.ai) | Acesso ao modelo `openai/gpt-4.1-mini` (tools + saída estruturada strict, com `require_parameters`) |
| [DummyJSON](https://dummyjson.com) | Catálogo de produtos (`/products/search`, `/products/{id}`, `/products/category/{c}`) |

## O que ficou de fora, de propósito

| Alternativa | Por que não |
|---|---|
| Framework de agentes (LangChain, LangGraph etc.) | O case pede que o modelo decida as tools; um loop próprio deixa isso explícito e testável |
| uv / poetry | pip com versões fixadas deixa o Dockerfile simples e reprodutível |
| `dataclass` | Pydantic em todo dado, para validação uniforme |
| Tailwind / biblioteca de UI | O chat é pequeno; CSS simples basta |
