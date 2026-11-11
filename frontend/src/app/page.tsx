import { Chat } from "@/components/Chat";

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
