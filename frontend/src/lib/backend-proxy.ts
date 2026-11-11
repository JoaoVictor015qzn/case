/** Repassa a chamada do browser para o FastAPI. A URL interna nunca chega ao cliente. */
export class BackendProxy {
  private static readonly FORWARDED_HEADERS = ["content-type", "idempotency-key", "x-request-id"];
  private static readonly DEFAULT_TIMEOUT_MS = 120_000;
  private static readonly TIMEOUT_DETAIL =
    "O agente demorou demais para responder. Tente novamente.";
  private static readonly UNREACHABLE_DETAIL =
    "Não foi possível falar com o backend. Verifique se ele está no ar.";

  async forward(path: string, request: Request): Promise<Response> {
    const body = request.method === "GET" ? undefined : await request.text();
    try {
      const response = await fetch(`${this.baseUrl()}${path}`, {
        method: request.method,
        headers: this.forwardedHeaders(request),
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(this.timeoutMs()),
      });
      return new Response(await response.text(), {
        status: response.status,
        headers: {
          "content-type": response.headers.get("content-type") ?? "application/json",
          "x-request-id": response.headers.get("x-request-id") ?? "",
        },
      });
    } catch (error) {
      return this.failure(error);
    }
  }

  private failure(error: unknown): Response {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    const detail = timedOut ? BackendProxy.TIMEOUT_DETAIL : BackendProxy.UNREACHABLE_DETAIL;
    return Response.json({ detail, missing: [], toolCalls: [] }, { status: timedOut ? 504 : 502 });
  }

  private forwardedHeaders(request: Request): Headers {
    const headers = new Headers();
    for (const name of BackendProxy.FORWARDED_HEADERS) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }
    return headers;
  }

  private baseUrl(): string {
    return process.env.BACKEND_URL ?? "http://localhost:8000";
  }

  private timeoutMs(): number {
    const configured = Number(process.env.BACKEND_TIMEOUT_MS);
    return Number.isFinite(configured) && configured > 0
      ? configured
      : BackendProxy.DEFAULT_TIMEOUT_MS;
  }
}
