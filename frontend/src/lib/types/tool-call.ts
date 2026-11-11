export type ToolCall = {
  name: string;
  arguments: Record<string, unknown>;
  isError: boolean;
  durationMs: number;
};
