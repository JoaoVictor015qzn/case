import { ErrorMessageTranslator } from "@/lib/error-message-translator";
import type { CreateRequisitionResponse } from "@/lib/types/create-requisition-response";
import type { CreateRequisitionResult } from "@/lib/types/create-requisition-result";

/** Cliente do browser: só conhece o BFF do próprio Next (`/api/requisicoes`). */
export class RequisitionsClient {
  constructor(
    private readonly endpoint = "/api/requisicoes",
    private readonly translator = new ErrorMessageTranslator(),
  ) {}

  async create(requestText: string, idempotencyKey: string): Promise<CreateRequisitionResult> {
    let response: Response;
    try {
      response = await fetch(this.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({ requestText }),
      });
    } catch {
      return { ok: false, status: 0, error: this.translator.network() };
    }
    const body = await this.readJson(response);
    if (response.ok) {
      return { ok: true, data: body as CreateRequisitionResponse };
    }
    return {
      ok: false,
      status: response.status,
      error: this.translator.fromResponse(response.status, body),
    };
  }

  private async readJson(response: Response): Promise<unknown> {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
}
