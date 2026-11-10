# Referência oficial: OpenRouter e cliente MCP

## OpenRouter: SDK OpenAI como drop-in (openrouter.ai/docs/quickstart)

```python
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="<OPENROUTER_API_KEY>",
)

response = client.responses.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>",   # opcional
    "X-OpenRouter-Title": "<YOUR_SITE_NAME>",  # opcional
  },
  model="~openai/gpt-sol-latest",
  input="What is the meaning of life?"
)
print(response.output_text)
```

No backend, use `AsyncOpenAI`, que tem a mesma API com `await`.

## OpenRouter: tool calling, formato da Responses API (guides/features/tool-calling)

Definição da tool:

```json
{
  "type": "function",
  "name": "search_gutenberg_books",
  "description": "Search for books in the Project Gutenberg library",
  "parameters": {
    "type": "object",
    "properties": {"search_terms": {"type": "array", "items": {"type": "string"}}},
    "required": ["search_terms"],
    "additionalProperties": false
  }
}
```

"On both APIs, the `tools` parameter must be included in every request (Steps 1 and 3) so the router can validate the tool schema on each call."

### Loop agêntico oficial (Python)

```python
def call_llm(items):
    resp = openai_client.responses.create(
        model=MODEL,
        instructions=instructions,
        tools=tools,
        input=items
    )
    if resp.status != "completed":
        message = resp.error.message if resp.error else f"Response ended as {resp.status}"
        raise RuntimeError(message)
    items += resp.output
    return resp

def get_tool_response(tool_call):
    tool_name = tool_call.name
    tool_args = json.loads(tool_call.arguments)
    tool_result = TOOL_MAPPING[tool_name](**tool_args)
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(tool_result),
    }

max_iterations = 10
iteration_count = 0
final_text = None

while iteration_count < max_iterations:
    iteration_count += 1
    resp = call_llm(input_items)
    tool_calls = [item for item in resp.output if item.type == "function_call"]
    if not tool_calls:
        final_text = resp.output_text
        break
    for tool_call in tool_calls:
        input_items.append(get_tool_response(tool_call))

if final_text is None:
    print("Warning: Maximum iterations reached")
```

No nosso caso, `TOOL_MAPPING[...]` é substituído por `await mcp.call_tool(name, args)`.

### Boas práticas da doc

- Use nomes claros e específicos (`get_weather_forecast`, e não `weather`).
- Descrições detalhadas, com exemplos de valores nos parâmetros.
- "Error Handling: Design tools to provide meaningful error messages that help the model adjust its approach."
- `tool_choice`: `"auto"` (default) deixa o modelo decidir. **Mantenha `auto`**, porque é o requisito do case.
- `parallel_tool_calls` é `true` por padrão na maioria dos modelos. O loop precisa tratar várias `function_call` numa mesma resposta.

## OpenRouter: structured outputs (guides/features/structured-outputs)

```json
{
  "text": {
    "format": {
      "type": "json_schema",
      "name": "weather",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "City or location name"}},
        "required": ["location"],
        "additionalProperties": false
      }
    }
  }
}
```

- O suporte é por modelo e por provider. Para garantir o roteamento, filtre por `supported_parameters` e envie `provider: {"require_parameters": true}`.
- Com `strict: true`, alguns providers restringem features do JSON Schema. Se o provider rejeitar `minimum` ou `anyOf`, simplifique o schema e valide com Pydantic depois.
- Existe o plugin "Response Healing", que corrige JSON malformado em requests sem streaming.

## OpenRouter: erros (api/reference/errors-and-debugging)

Formato: `{"error": {"code": number, "message": string, "metadata"?: {...}}}`.

| Código | Significado |
|---|---|
| 400 | Requisição inválida (parâmetros ou CORS) |
| 401 | Credenciais inválidas (chave errada ou expirada) |
| 402 | Sem créditos |
| 403 | Moderação, guardrail ou orçamento |
| 408 | Timeout |
| 429 | Rate limit (vem com `Retry-After`) |
| 502 | Modelo fora do ar ou resposta inválida |
| 503 | Nenhum provider atende os requisitos de roteamento |

"The OpenAI SDK [...] already respect this header for backoff on the statuses each SDK retries automatically. None of them retries a `402`."

Atenção: erros que acontecem **durante** a geração podem vir com HTTP 200 e o erro no corpo. Por isso é preciso checar `resp.status != "completed"`.

## Cliente MCP v2 (py.sdk.modelcontextprotocol.io/client/)

```python
from mcp import Client

async with Client("http://mcp-server:8000/mcp") as client:
    result = await client.list_tools()
    for tool in result.tools:
        tool.name, tool.description, tool.input_schema  # input_schema já é JSON Schema

    result = await client.call_tool("lookup_book", {"title": "Dune"})
    result.content             # lista de TextContent/ImageContent... (narrow com isinstance)
    result.structured_content  # dict, para o código
    result.is_error            # cheque antes de confiar em structured_content
```

- "A tool that raises does not raise in your client. It comes back as an ordinary result with `is_error=True`."
- Uma tool inexistente também volta como `is_error=True` ("Unknown tool: ...").
- O timeout padrão do transporte HTTP é de 30s para connect/write e 300s para read. Para mudar, passe o seu próprio `httpx2.AsyncClient(timeout=httpx2.Timeout(30.0, read=...))` para `streamable_http_client(url, http_client=...)`. Desde a v2, `streamable_http_client` **não** aceita `headers=` nem `timeout=`.
- A v2 usa `httpx2` (não `httpx`). Capture `httpx2.ConnectError` e similares para detectar o MCP fora do ar.
