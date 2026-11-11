"use client";

import { useState } from "react";

import { ChatInput } from "@/components/ChatInput";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatMessageFactory } from "@/lib/chat-message-factory";
import { RequisitionsClient } from "@/lib/requisitions-client";
import type { ChatMessage } from "@/lib/types/chat-message";

const client = new RequisitionsClient();
const factory = new ChatMessageFactory();

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);

  async function send(text: string) {
    setMessages((current) => [...current, factory.user(text)]);
    setSending(true);
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
