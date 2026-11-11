import type { Metadata } from "next";
import "./globals.css";

// Título e descrição da aplicação usados nas tags <head>.
export const metadata: Metadata = {
  title: "Agente de compras",
  description: "Transforma pedidos em texto em requisições de compra.",
};

// Layout raiz: define o idioma pt-BR e envolve todas as páginas.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
