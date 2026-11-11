// Registro de uma ferramenta MCP chamada pelo agente: nome, argumentos, falha e duração.
export type ToolCall = {
  name: string;
  arguments: Record<string, unknown>;
  isError: boolean;
  durationMs: number;
};
