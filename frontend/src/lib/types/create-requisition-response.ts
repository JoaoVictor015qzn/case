import type { Requisition } from "@/lib/types/requisition";
import type { ToolCall } from "@/lib/types/tool-call";

export type CreateRequisitionResponse = {
  requisition: Requisition;
  message: string;
  missing: string[];
  toolCalls: ToolCall[];
  replayed: boolean;
};
