# Referência oficial: MCP Python SDK v2

Docs: https://py.sdk.modelcontextprotocol.io/ (a versão estável no PyPI é `mcp` 2.x; requer Python 3.11+)

## Instalação

```bash
uv add "mcp[cli]"      # ou: pip install "mcp[cli]"
```

## Tool mínima (servers/tools)

```python
from mcp.server import MCPServer

mcp = MCPServer("Bookshop")

@mcp.tool()
def search_books(query: str, limit: int) -> str:
    """Search the catalog by title or author."""
    return f"Found 3 books matching {query!r} (showing up to {limit})."
```

- O nome da tool é o nome da função, e a descrição é a docstring.
- O input schema é gerado a partir dos type hints.
- Um parâmetro com default deixa de ser obrigatório.

## Schemas ricos com `Field` e anotações

```python
from typing import Annotated, Literal
from pydantic import Field
from mcp.server import MCPServer

mcp = MCPServer("Bookshop")

@mcp.tool()
def search_books(
    query: Annotated[str, Field(description="Title or author to search for.")],
    limit: Annotated[int, Field(ge=1, le=50, description="Maximum number of results.")] = 10,
    genre: Literal["fiction", "non-fiction", "poetry"] | None = None,
) -> str:
    """Search the catalog by title or author."""
    ...
```

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    title="Search the catalog",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def search_books(query: str) -> str: ...
```

"Use `async def` se a tool faz I/O. Uma tool `def` roda numa thread."

## Erros (servers/handling-errors)

```python
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("Bookshop")
CATALOG = {"Dune": "Frank Herbert", "Neuromancer": "William Gibson"}

@mcp.tool()
def get_author(title: str) -> str:
    """Look up the author of a book in the catalog."""
    if title not in CATALOG:
        raise ToolError(f"No book titled {title!r} in the catalog.")
    return CATALOG[title]
```

Resultado: `is_error=True` e `content=[TextContent(text="Error executing tool get_author: No book titled ...")]`.

- "Never `return` an error message from a tool." Um retorno tem `is_error=False`.
- `ToolError` serve para falhas de execução, como um upstream que deu timeout ou um registro inexistente.
- `MCPError` serve para rejeitar a requisição em si, por exemplo quando falta uma capability.
- Qualquer outra exceção vira "Error executing tool <name>". O modelo não vê a mensagem, e o log recebe o traceback em `ERROR`.

## Lifespan tipado (handlers/lifespan)

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server import MCPServer
from mcp.server.mcpserver import Context

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()

mcp = MCPServer("Bookshop", lifespan=app_lifespan)

@mcp.tool()
def count_books(genre: str, ctx: Context[AppContext]) -> str:
    """Count the books in a genre."""
    db = ctx.request_context.lifespan_context.db
    return f"{db.query()} books in {genre!r}."
```

- O parâmetro `ctx` é injetado e **não** aparece no input schema.
- No Streamable HTTP v2, o lifespan roda **uma vez** no startup e é compartilhado por todas as requests. É o lugar certo para um pool de conexões ou um `httpx.AsyncClient`.

## Rodando (run/)

```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=3001)
```

- Opções de `run()`: `host` (default `127.0.0.1`, use `0.0.0.0` no Docker), `port` (default 8000), `streamable_http_path` (default `/mcp`), `json_response`, `stateless_http` e `transport_security`.
- "Transport options go to `run()`, not to `MCPServer(...)`."
- Para um servidor de produção, construa o app ASGI com `mcp.streamable_http_app(transport_security=...)` e sirva com uvicorn.

## Host allowlist (run/deploy): obrigatório no Docker

```python
from mcp.server.transport_security import TransportSecuritySettings

security = TransportSecuritySettings(
    allowed_hosts=["mcp.example.com", "mcp.example.com:*"],
    allowed_origins=["https://app.example.com"],
)
app = mcp.streamable_http_app(transport_security=security)
```

Sem isso, todo `Host` diferente de localhost recebe `421 Misdirected Request — Invalid Host header`. "A freshly deployed server that refuses every connection is a Host allowlist until proven otherwise."

A doc também diz: "No health-check route. `@mcp.custom_route("/health", methods=["GET"])` is the whole answer."

## Cliente (client/)

```python
from mcp import Client

async with Client("http://localhost:8000/mcp") as client:
    tools = await client.list_tools()            # tool.name, tool.description, tool.input_schema
    result = await client.call_tool("add", {"a": 1, "b": 2})
    result.content             # para o modelo (TextContent etc.)
    result.structured_content  # para o código
    result.is_error            # sempre cheque antes de confiar em structured_content
```

- Uma tool que levanta exceção **não** levanta no cliente. O cliente recebe `is_error=True`.
- `MCPError` só é levantado quando o servidor responde com um erro JSON-RPC.

## Testes (get-started/testing)

```python
import pytest
from inline_snapshot import snapshot
from mcp import Client
from mcp.types import CallToolResult, TextContent

from server import mcp

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        yield c

@pytest.mark.anyio
async def test_call_add_tool(client: Client):
    result = await client.call_tool("add", {"a": 1, "b": 2})
    result.meta = None
    assert result == snapshot(
        CallToolResult(
            content=[TextContent(type="text", text="3")],
            structured_content={"result": 3},
        )
    )
```

- "No subprocess, no port, no transport. `Client(mcp)` connects to the server object directly."
- `raise_exceptions=True` faz o teste ver a mensagem real de falhas fora da tool. Use sempre nos testes.

## Mock do httpx para o adapter (python-httpx.org/advanced/transports)

```python
def handler(request):
    return httpx.Response(200, json={"text": "Hello, world!"})

client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://dummyjson.com")
```

Para simular um timeout: `raise httpx.ReadTimeout("timeout", request=request)` dentro do handler.

## DummyJSON (dummyjson.com/docs/products)

- `GET /products/search?q=phone` retorna `{"products": [...], "total": 23, "skip": 0, "limit": 23}`.
- `GET /products/1` retorna um produto com `id, title, description, category, price, discountPercentage, rating, stock, tags, brand, sku, availabilityStatus, minimumOrderQuantity, ...`.
- `select=title,price` reduz os campos retornados, e `limit` e `skip` fazem a paginação (`limit=0` traz todos).
- As categorias incluem `laptops`, `smartphones`, `tablets` e `mobile-accessories`.
- O catálogo é em inglês e os preços estão em USD.
