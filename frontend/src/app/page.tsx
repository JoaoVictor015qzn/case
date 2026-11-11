import { Chat } from "@/components/Chat";

// Página inicial: cabeçalho com instruções e o chat do agente de compras.
export default function Home() {
  return (
    <main className="page">
      <header className="page-header">
        <h1>Agente de compras</h1>
        <p className="muted">Peça em texto livre; a requisição usa só produtos reais do catálogo.</p>
      </header>
      <Chat />
    </main>
  );
}
