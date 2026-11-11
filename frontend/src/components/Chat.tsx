"use client";

import { useState } from "react";

import { ChatInput } from "@/components/ChatInput";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatMessageFactory } from "@/lib/chat-message-factory";
import { RequisitionsClient } from "@/lib/requisitions-client";
import type { ChatMessage } from "@/lib/types/chat-message";

// Instâncias únicas compartilhadas entre renderizações do chat.
const client = new RequisitionsClient();
const factory = new ChatMessageFactory();

// Chat principal: guarda o histórico de mensagens e envia pedidos ao BFF.
export function Chat() {
  // Estado do chat: mensagens exibidas e indicador de envio em andamento.
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);

  // Mostra a mensagem do usuário, chama o BFF e acrescenta a resposta ou o erro.
  async function send(text: string) {
    setMessages((current) => [...current, factory.user(text)]);
    setSending(true);
    // Cada envio gera uma Idempotency-Key nova para o backend não duplicar requisições.
    const result = await client.create(text, crypto.randomUUID());
    const reply = result.ok ? factory.fromRequisition(result.data) : factory.fromError(result.error);
    setMessages((current) => [...current, reply]);
    setSending(false);
  }

  return (
    <div className="chat">
      <ol className="messages" aria-live="polite">
        {messages.length === 0 && (
          <li className="empty">
            Descreva o que precisa comprar. O agente consulta o catálogo e monta a requisição só
            com produtos que existem.
          </li>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {sending && <li className="bubble bubble-agent pending">Consultando catálogo…</li>}
      </ol>
      <ChatInput disabled={sending} onSend={send} />
    </div>
  );
}
