import type { Money } from "@/lib/types/money";

// Item da requisição: produto do catálogo, quantidade, preço unitário e subtotal.
export type RequisitionItem = {
  productId: number;
  title: string;
  unitPrice: Money;
  quantity: number;
  lineTotal: Money;
};
