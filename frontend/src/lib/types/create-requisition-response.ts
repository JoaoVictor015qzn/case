import type { Requisition } from "@/lib/types/requisition";
import type { ToolCall } from "@/lib/types/tool-call";

// Resposta de sucesso do POST /requisicoes; replayed indica requisição já criada antes.
export type CreateRequisitionResponse = {
  requisition: Requisition;
  message: string;
  missing: string[];
  toolCalls: ToolCall[];
  replayed: boolean;
};
