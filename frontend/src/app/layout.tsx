import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agente de compras",
  description: "Transforma pedidos em texto em requisições de compra.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
