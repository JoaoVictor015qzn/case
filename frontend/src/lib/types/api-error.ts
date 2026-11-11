import type { ToolCall } from "@/lib/types/tool-call";

export type ApiError = {
  detail: string;
  missing: string[];
  toolCalls: ToolCall[];
};
