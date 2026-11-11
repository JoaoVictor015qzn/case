import type { ApiError } from "@/lib/types/api-error";
import type { ChatMessage } from "@/lib/types/chat-message";
import type { CreateRequisitionResponse } from "@/lib/types/create-requisition-response";

export class ChatMessageFactory {
  user(text: string): ChatMessage {
    return this.base("user", text);
  }

  fromRequisition(response: CreateRequisitionResponse): ChatMessage {
    return {
      ...this.base("agent", response.message),
      requisition: response.requisition,
      missing: response.missing,
      toolCalls: response.toolCalls,
      replayed: response.replayed,
    };
  }

  fromError(error: ApiError): ChatMessage {
    return {
      ...this.base("agent", error.detail),
      missing: error.missing,
      toolCalls: error.toolCalls,
      isError: error.missing.length === 0,
    };
  }

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
