import type { ToolCall } from "@/lib/types/tool-call";

// Lista recolhível das ferramentas MCP chamadas, com argumentos, resultado e duração.
export function ToolCallList({ toolCalls }: { toolCalls: ToolCall[] }) {
  if (toolCalls.length === 0) return null;
  return (
    <details className="tool-calls">
      <summary>Ferramentas consultadas ({toolCalls.length})</summary>
      <ul>
        {toolCalls.map((call, index) => (
          <li key={`${call.name}-${index}`}>
            <span aria-label={call.isError ? "falhou" : "ok"}>{call.isError ? "✗" : "✓"}</span>{" "}
            <code>{call.name}</code> <code>{JSON.stringify(call.arguments)}</code>{" "}
            <span className="muted">{call.durationMs} ms</span>
          </li>
        ))}
      </ul>
    </details>
  );
}
