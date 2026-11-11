import { BackendProxy } from "@/lib/backend-proxy";

const proxy = new BackendProxy();

// Cria uma requisição repassando o pedido do chat para o backend FastAPI.
export async function POST(request: Request) {
  return proxy.forward("/requisicoes", request);
}

// Lista requisições repassando a consulta para o backend FastAPI.
export async function GET(request: Request) {
  return proxy.forward("/requisicoes", request);
}
