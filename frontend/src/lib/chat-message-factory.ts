import type { ApiError } from "@/lib/types/api-error";
import type { ChatMessage } from "@/lib/types/chat-message";
import type { CreateRequisitionResponse } from "@/lib/types/create-requisition-response";

// Monta as mensagens do chat a partir do texto do usuário, da resposta ou do erro da API.
export class ChatMessageFactory {
  // Mensagem enviada pelo usuário.
  user(text: string): ChatMessage {
    return this.base("user", text);
  }

  // Resposta do agente com a requisição criada, o que faltou e as ferramentas chamadas.
  fromRequisition(response: CreateRequisitionResponse): ChatMessage {
    return {
      ...this.base("agent", response.message),
      requisition: response.requisition,
      missing: response.missing,
      toolCalls: response.toolCalls,
      replayed: response.replayed,
    };
  }

  // Resposta de erro; só é destacada como erro quando não há itens faltantes a explicar.
  fromError(error: ApiError): ChatMessage {
    return {
      ...this.base("agent", error.detail),
      missing: error.missing,
      toolCalls: error.toolCalls,
      isError: error.missing.length === 0,
    };
  }

  // Mensagem com id único e campos opcionais vazios.
  private base(role: ChatMessage["role"], text: string): ChatMessage {
    return {
      id: crypto.randomUUID(),
      role,
      text,
      missing: [],
      toolCalls: [],
      isError: false,
      replayed: false,
    };
  }
}
