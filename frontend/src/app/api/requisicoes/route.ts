import { BackendProxy } from "@/lib/backend-proxy";

const proxy = new BackendProxy();

export async function POST(request: Request) {
  return proxy.forward("/requisicoes", request);
}

export async function GET(request: Request) {
  return proxy.forward("/requisicoes", request);
}
