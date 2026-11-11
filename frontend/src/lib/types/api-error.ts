import type { ToolCall } from "@/lib/types/tool-call";

// Corpo de erro da API: mensagem, itens não atendidos e ferramentas chamadas.
export type ApiError = {
  detail: string;
  missing: string[];
  toolCalls: ToolCall[];
};
