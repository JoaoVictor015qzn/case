import json
from typing import Any

import httpx2
from openai import AsyncOpenAI

from app.schemas.agent.requisition_draft import RequisitionDraft


class ScriptedOpenRouter:
    """OpenRouter falsa: devolve respostas da Responses API em sequência e guarda cada request."""

    def __init__(self, *responses: dict[str, Any] | httpx2.Response) -> None:
        self._responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    # SDK openai real apontado para o transporte falso, sem retries.
    def client(self) -> AsyncOpenAI:
        transport = httpx2.MockTransport(self._handle)
        return AsyncOpenAI(
            api_key="test-key",
            base_url="https://openrouter.test/api/v1",
            max_retries=0,
            http_client=httpx2.AsyncClient(transport=transport),
        )

    # Guarda o corpo enviado e devolve a próxima resposta do roteiro (JSON ou Response pronta).
    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(json.loads(request.content))
        scripted = self._responses.pop(0)
        return (
            scripted
            if isinstance(scripted, httpx2.Response)
            else httpx2.Response(200, json=scripted)
        )

    # Resposta em que o modelo pede a execução de uma tool.
    @staticmethod
    def function_call(
        name: str, arguments: dict[str, Any], call_id: str = "call_1"
    ) -> dict[str, Any]:
        item = {
            "type": "function_call",
            "id": f"fc_{call_id}",
            "call_id": call_id,
            "name": name,
            "arguments": json.dumps(arguments),
            "status": "completed",
        }
        return ScriptedOpenRouter._response([item])

    # Resposta final do modelo com texto, sem tool calls.
    @staticmethod
    def final_text(text: str) -> dict[str, Any]:
        item = {
            "type": "message",
            "id": "msg_1",
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}],
        }
        return ScriptedOpenRouter._response([item])

    # Resposta final cujo texto é o rascunho serializado em JSON (saída estruturada).
    @classmethod
    def final_draft(cls, draft: RequisitionDraft) -> dict[str, Any]:
        return cls.final_text(draft.model_dump_json())

    # Envelope mínimo de um objeto response da Responses API com a saída dada.
    @staticmethod
    def _response(output: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": "resp_1",
            "object": "response",
            "created_at": 0,
            "model": "openai/gpt-4.1-mini",
            "status": "completed",
            "output": output,
            "parallel_tool_calls": True,
            "tool_choice": "auto",
            "tools": [],
            "usage": {
                "input_tokens": 10,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens": 5,
                "output_tokens_details": {"reasoning_tokens": 0},
                "total_tokens": 15,
            },
        }
