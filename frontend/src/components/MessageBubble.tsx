import { MissingList } from "@/components/MissingList";
import { RequisitionCard } from "@/components/RequisitionCard";
import { ToolCallList } from "@/components/ToolCallList";
import type { ChatMessage } from "@/lib/types/chat-message";

// Balão de mensagem: texto, requisição criada, itens não atendidos e ferramentas usadas.
export function MessageBubble({ message }: { message: ChatMessage }) {
  // Classes CSS conforme o autor da mensagem e se ela representa um erro.
  const classes = ["bubble", `bubble-${message.role}`, message.isError ? "bubble-error" : ""];
  return (
    <li className={classes.join(" ")}>
      <p role={message.isError ? "alert" : undefined}>{message.text}</p>
      {message.requisition && (
        <RequisitionCard requisition={message.requisition} replayed={message.replayed} />
      )}
      <MissingList missing={message.missing} />
      <ToolCallList toolCalls={message.toolCalls} />
    </li>
  );
}
