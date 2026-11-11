"use client";

import { useState, type FormEvent, type KeyboardEvent } from "react";

const MIN_LENGTH = 3;
const MAX_LENGTH = 1000;

export function ChatInput({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");
  const trimmed = text.trim();
  const canSend = !disabled && trimmed.length >= MIN_LENGTH;

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSend) return;
    onSend(trimmed);
    setText("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form className="chat-input" onSubmit={submit}>
      <label htmlFor="request-text">O que você precisa comprar?</label>
      <textarea
        id="request-text"
        value={text}
        maxLength={MAX_LENGTH}
        rows={2}
        placeholder="Ex.: Preciso de 2 notebooks para a equipe de vendas, até 1500 dólares cada"
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button type="submit" disabled={!canSend}>
        {disabled ? "Consultando catálogo…" : "Enviar"}
      </button>
    </form>
  );
}
