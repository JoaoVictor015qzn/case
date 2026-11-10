# Referência oficial: Next.js

Fontes:
- https://nextjs.org/docs/app/getting-started/route-handlers
- https://nextjs.org/docs/app/api-reference/config/next-config-js/output
- https://github.com/vercel/next.js/tree/canary/examples/with-docker

## Route Handlers

```ts
// app/api/route.ts
export async function GET(request: Request) {}
```

- Métodos suportados: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` e `OPTIONS`. Um método não suportado retorna 405.
- "Route Handlers are not cached by default."
- "There cannot be a `route.js` file at the same route segment level as `page.js`."

| Page | Route | Resultado |
|---|---|---|
| `app/page.js` | `app/route.js` | ✗ Conflito |
| `app/page.js` | `app/api/route.js` | ✓ Válido |

Exemplo oficial chamando uma API externa com uma variável de ambiente do servidor:

```ts
export async function GET() {
  const res = await fetch('https://data.mongodb-api.com/...', {
    headers: {
      'Content-Type': 'application/json',
      'API-Key': process.env.DATA_API_KEY,
    },
  })
  const data = await res.json()
  return Response.json({ data })
}
```

## Saída standalone

```js
// next.config.js
module.exports = {
  output: 'standalone',
}
```

- O build gera `.next/standalone` com um `server.js` mínimo.
- "This minimal server does not copy the `public` or `.next/static` folders by default [...] these folders can be copied to the `standalone/public` and `standalone/.next/static` folders manually."
- "If your project needs to listen to a specific port or hostname, you can define `PORT` or `HOSTNAME` environment variables before running `server.js`."

## Dockerfile oficial (examples/with-docker), essencial

```dockerfile
ARG NODE_VERSION=24.13.0-slim

FROM node:${NODE_VERSION} AS dependencies
WORKDIR /app
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* pnpm-workspace.yaml* .npmrc* ./
RUN --mount=type=cache,target=/root/.npm \
  if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; \
  else echo "No lockfile found." && exit 1; fi

FROM node:${NODE_VERSION} AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=production
RUN npm run build

FROM node:${NODE_VERSION} AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
COPY --from=builder --chown=node:node /app/public ./public
RUN mkdir .next
RUN chown node:node .next
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

O exemplo original detecta yarn, npm ou pnpm. Como usamos npm, o trecho acima foi simplificado para npm.

Para desligar a telemetria no build e no runtime, use `ENV NEXT_TELEMETRY_DISABLED=1`.
