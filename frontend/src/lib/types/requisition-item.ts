import type { Money } from "@/lib/types/money";

export type RequisitionItem = {
  productId: number;
  title: string;
  unitPrice: Money;
  quantity: number;
  lineTotal: Money;
};
