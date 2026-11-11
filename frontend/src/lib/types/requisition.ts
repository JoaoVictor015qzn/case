import type { Money } from "@/lib/types/money";
import type { RequisitionItem } from "@/lib/types/requisition-item";

// Requisição de compra persistida: itens, total, status e o que ficou faltando.
export type Requisition = {
  id: number;
  requestText: string;
  status: "complete" | "partial";
  items: RequisitionItem[];
  total: Money;
  message: string;
  missing: string[];
  createdAt: string;
};
