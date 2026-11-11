---
name: nextjs-chat
description: Constrói o chat do case em Next.js (App Router, TypeScript) - Route Handler como BFF que faz proxy para o backend FastAPI, componentes de chat, exibição da requisição criada (número, itens, total), do que falta, das ferramentas chamadas e mensagens de erro claras; build standalone em Docker conforme exemplo oficial. Use ao criar ou alterar qualquer coisa em frontend/.
---

# Chat em Next.js (App Router)

Exemplos oficiais: [reference.md](reference.md).

## Arquitetura (BFF)

```
Browser ──fetch('/api/requisicoes')──► Next.js Route Handler (server) ──fetch(BACKEND_URL)──► FastAPI
```

- O browser **só** fala com o próprio Next. A URL interna (`http://backend:8000`) fica no servidor, o que dispensa CORS e não expõe a topologia.
- `BACKEND_URL` é lida em `process.env` **no runtime**. Não use o prefixo `NEXT_PUBLIC_`, porque ele embute o valor no bundle durante o build.
- O Route Handler aplica um timeout (`AbortSignal.timeout`) e converte falhas de rede em `{detail}` legível.

## Estrutura

Mesma filosofia do backend: um componente ou classe por arquivo, tipos de dados separados por assunto em `lib/types/`. Componentes React continuam sendo funções (é o idioma do React); a lógica fora dos componentes (cliente HTTP, formatação, tradução de erros) fica em classes. Estilo decidido com o usuário.

```
frontend/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                      # server component: renderiza <Chat />
│   └── api/requisicoes/route.ts      # POST e GET -> backend
├── components/
│   ├── Chat.tsx                      # "use client": estado da conversa
│   ├── ChatInput.tsx
│   ├── MessageBubble.tsx
│   ├── RequisitionCard.tsx           # nº, itens, quantidade, preço, total
│   └── ToolCallList.tsx              # diferencial: ferramentas chamadas
└── lib/
    ├── types/                        # espelho dos DTOs do backend, um arquivo por assunto
    ├── requisitions-client.ts        # RequisitionsClient: fetch para /api/requisicoes
    └── money-formatter.ts            # MoneyFormatter: Intl.NumberFormat USD
```

## Route Handler (proxy)

```ts
// src/app/api/requisicoes/route.ts
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const TIMEOUT_MS = Number(process.env.BACKEND_TIMEOUT_MS ?? 120_000);

export async function POST(request: Request) {
  const body = await request.json();
  try {
    const res = await fetch(`${BACKEND_URL}/requisicoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return Response.json(await res.json(), { status: res.status });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    return Response.json(
      { detail: timedOut ? "O agente demorou demais para responder. Tente novamente."
                         : "Não foi possível falar com o backend. Verifique se ele está no ar." },
      { status: timedOut ? 504 : 502 },
    );
  }
}

export async function GET() { /* mesmo padrão, para GET /requisicoes */ }
```

Regras:
- Route Handlers não são cacheados por padrão. Não adicione `dynamic = 'force-static'`.
- Não pode haver `route.ts` e `page.tsx` no mesmo segmento. Por isso o proxy fica em `app/api/...`.

## Componentes

- Só o que tem estado ou evento recebe `"use client"`. Em geral, só `Chat.tsx` e `ChatInput.tsx`.
- O estado é uma lista de `ChatMessage`: `{ role: "user" | "agent", text, requisition?, missing?, toolCalls?, error? }`.
- Estados visíveis obrigatórios:
  - **enviando**: botão desabilitado e indicador "Consultando catálogo…";
  - **sucesso**: `RequisitionCard` com **"Requisição nº {id}"**, uma tabela de itens (produto, qtd, preço unitário, subtotal) e o total;
  - **nada atende (422)**: a mensagem do agente e a lista `missing`;
  - **erro (5xx)**: o `detail` do backend em destaque. É o requisito "se a DummyJSON falhar, o chat mostra uma mensagem clara".
- Mostre `toolCalls` em um `<details>` colapsável, com o nome da tool, os argumentos, ✓/✗ e a duração.
- Formate moeda com `new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" })`.
- Acessibilidade: `<form>` com `<label>`, envio por Enter e `aria-live="polite"` na lista de mensagens.
- Não guarde segredo nem chave no front.

## Tipos (espelham o backend)

```ts
// dinheiro chega como objeto, com amount em string decimal (nunca converter para number para somar)
export type Money = { amount: string; currency: "USD" };
export type RequisitionItem = { productId: number; title: string; unitPrice: Money; quantity: number; lineTotal: Money };
export type Requisition = { id: number; status: "complete" | "partial"; items: RequisitionItem[]; total: Money; createdAt: string };
export type ToolCall = { name: string; arguments: Record<string, unknown>; isError: boolean; durationMs: number };
export type CreateRequisitionResponse = { requisition: Requisition; message: string; missing: string[]; toolCalls: ToolCall[] };
export type ApiError = { detail: string; missing?: string[]; toolCalls?: ToolCall[] };
```

Decisão: valores `Decimal` chegam como **string** no JSON, e o front só formata, sem fazer conta. Combine a convenção de nomes com o backend. O mais simples é o backend expor camelCase via `alias_generator=to_camel` com `serialize_by_alias`, ou o front usar snake_case. Escolha uma opção e documente.

## Docker (exemplo oficial `with-docker`)

- O serviço tem seu próprio `frontend/compose.yml` (porta 3000, `BACKEND_URL: http://backend:8000`, `depends_on: backend: condition: service_healthy`), incluído pelo `compose.yml` da raiz (skill `docker-compose`).
- `next.config.ts` usa `output: "standalone"`.
- Dockerfile multi-stage em 3 estágios (dependencies, builder e runner), com `node:24-slim`, `USER node`, `ENV HOSTNAME="0.0.0.0"` e `CMD ["node", "server.js"]`.
- Copie `.next/static` e `public` para a imagem final. O standalone não copia esses dois sozinho.
- A pasta `public/` precisa existir, porque o `COPY` falha sem ela.

## Setup

```bash
npx create-next-app@latest frontend --ts --app --src-dir --eslint --use-npm
```

Se o pacote `next` instalado trouxer docs locais (`node_modules/next/dist/docs/`) ou um `AGENTS.md`, consulte esses arquivos antes de escrever código. Eles correspondem à versão instalada.

## Confirmado na implementação (Next 16.4.6)

- O `create-next-app` atual já liga `cacheComponents` e `partialPrefetching`. Um GET de Route Handler que faz `fetch` roda no request, então o proxy continua dinâmico.
- Sem `next/font/google`: ele baixa a fonte no build. Use fonte do sistema.
- O proxy mora na classe `BackendProxy` (`lib/backend-proxy.ts`); o `route.ts` só exporta `POST`/`GET` que delegam.
- `public/` tem um `.gitkeep`. O git não versiona pasta vazia e o `COPY public` quebraria num clone limpo.
- O browser gera um `Idempotency-Key` (`crypto.randomUUID()`) por envio. Um duplo clique não cria duas requisições.
- Ao testar no PowerShell 5: `Invoke-WebRequest` lê JSON sem charset como Latin-1, e script `.ps1` sem BOM corrompe acentos. Use `curl.exe` com corpo em arquivo.

## Checklist

- [ ] O browser não conhece a URL do backend, e não há `NEXT_PUBLIC_` com URL interna
- [ ] O proxy tem timeout, e os erros de rede viram `{detail}` claro
- [ ] O chat mostra o número da requisição, os itens, os preços e o total
- [ ] As telas de 422 e 5xx foram testadas manualmente, derrubando o mcp-server
- [ ] `npm run lint` e `npm run build` passam
