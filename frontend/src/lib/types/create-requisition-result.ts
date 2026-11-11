import type { ApiError } from "@/lib/types/api-error";
import type { CreateRequisitionResponse } from "@/lib/types/create-requisition-response";

// Resultado da chamada ao BFF: sucesso com os dados ou falha com status e erro traduzido.
export type CreateRequisitionResult =
  | { ok: true; data: CreateRequisitionResponse }
  | { ok: false; status: number; error: ApiError };
