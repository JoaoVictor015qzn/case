import type { ApiError } from "@/lib/types/api-error";
import type { CreateRequisitionResponse } from "@/lib/types/create-requisition-response";

export type CreateRequisitionResult =
  | { ok: true; data: CreateRequisitionResponse }
  | { ok: false; status: number; error: ApiError };
