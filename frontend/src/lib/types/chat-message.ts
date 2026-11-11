import type { Requisition } from "@/lib/types/requisition";
import type { ToolCall } from "@/lib/types/tool-call";

export type ChatMessage = {
  id: string;
  role: "user" | "agent";
  text: string;
  requisition?: Requisition;
  missing: string[];
  toolCalls: ToolCall[];
  isError: boolean;
  replayed: boolean;
};
