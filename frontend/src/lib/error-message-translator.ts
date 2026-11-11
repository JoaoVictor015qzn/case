import type { ApiError } from "@/lib/types/api-error";

/** Garante que toda falha vire uma mensagem legível, mesmo sem corpo JSON do backend. */
export class ErrorMessageTranslator {
  // Mensagens usadas quando a resposta de erro não traz um detail próprio.
  private static readonly FALLBACK_BY_STATUS: Record<number, string> = {
    422: "Não foi possível montar a requisição com esse pedido.",
    502: "O agente de IA falhou ao processar o pedido. Tente novamente.",
    503: "O catálogo de produtos está indisponível no momento. Tente novamente em instantes.",
    504: "O agente demorou demais para responder. Tente novamente.",
  };
  private static readonly DEFAULT_DETAIL = "Erro inesperado ao processar o pedido. Tente novamente.";
  private static readonly NETWORK_DETAIL =
    "Sem conexão com o servidor do chat. Verifique sua rede e tente novamente.";

  // Usa o detail do corpo quando existe; senão, a mensagem padrão do status HTTP.
  fromResponse(status: number, body: unknown): ApiError {
    if (this.isApiError(body)) {
      return { detail: body.detail, missing: body.missing ?? [], toolCalls: body.toolCalls ?? [] };
    }
    const detail =
      ErrorMessageTranslator.FALLBACK_BY_STATUS[status] ?? ErrorMessageTranslator.DEFAULT_DETAIL;
    return { detail, missing: [], toolCalls: [] };
  }

  // Erro para quando o navegador não consegue falar com o servidor do chat.
  network(): ApiError {
    return { detail: ErrorMessageTranslator.NETWORK_DETAIL, missing: [], toolCalls: [] };
  }

  // Verifica se o corpo é um objeto com campo detail em texto.
  private isApiError(body: unknown): body is Partial<ApiError> & { detail: string } {
    return (
      typeof body === "object" &&
      body !== null &&
      typeof (body as { detail?: unknown }).detail === "string"
    );
  }
}
