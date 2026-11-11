/** Repassa a chamada do browser para o FastAPI. A URL interna nunca chega ao cliente. */
export class BackendProxy {
  private static readonly FORWARDED_HEADERS = ["content-type", "idempotency-key", "x-request-id"];
  private static readonly DEFAULT_TIMEOUT_MS = 120_000;
  private static readonly TIMEOUT_DETAIL =
    "O agente demorou demais para responder. Tente novamente.";
  private static readonly UNREACHABLE_DETAIL =
    "Não foi possível falar com o backend. Verifique se ele está no ar.";

  // Encaminha a requisição ao backend e devolve status, corpo e X-Request-ID da resposta.
  async forward(path: string, request: Request): Promise<Response> {
    const body = request.method === "GET" ? undefined : await request.text();
    try {
      // Chamada ao backend sem cache, abortada se passar do tempo limite configurado.
      const response = await fetch(`${this.baseUrl()}${path}`, {
        method: request.method,
        headers: this.forwardedHeaders(request),
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(this.timeoutMs()),
      });
      // Repassa ao navegador o status e o corpo do backend sem reinterpretar.
      return new Response(await response.text(), {
        status: response.status,
        headers: {
          "content-type": response.headers.get("content-type") ?? "application/json",
          "x-request-id": response.headers.get("x-request-id") ?? "",
        },
      });
    } catch (error) {
      // Falha de rede ou timeout: responde com erro no mesmo formato do backend.
      return this.failure(error);
    }
  }

  // Converte timeout em 504 e backend inacessível em 502, com detail legível.
  private failure(error: unknown): Response {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    const detail = timedOut ? BackendProxy.TIMEOUT_DETAIL : BackendProxy.UNREACHABLE_DETAIL;
    return Response.json({ detail, missing: [], toolCalls: [] }, { status: timedOut ? 504 : 502 });
  }

  // Copia só os cabeçalhos permitidos (Content-Type, Idempotency-Key e X-Request-ID).
  private forwardedHeaders(request: Request): Headers {
    const headers = new Headers();
    for (const name of BackendProxy.FORWARDED_HEADERS) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }
    return headers;
  }

  // URL interna do backend, lida da variável BACKEND_URL no servidor.
  private baseUrl(): string {
    return process.env.BACKEND_URL ?? "http://localhost:8000";
  }

  // Tempo limite de BACKEND_TIMEOUT_MS; usa o padrão se ausente ou inválido.
  private timeoutMs(): number {
    const configured = Number(process.env.BACKEND_TIMEOUT_MS);
    return Number.isFinite(configured) && configured > 0
      ? configured
      : BackendProxy.DEFAULT_TIMEOUT_MS;
  }
}
