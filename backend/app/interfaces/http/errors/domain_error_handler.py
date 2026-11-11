import logging
from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors.agent_iteration_limit_error import AgentIterationLimitError
from app.domain.errors.agent_output_error import AgentOutputError
from app.domain.errors.catalog_unavailable_error import CatalogUnavailableError
from app.domain.errors.domain_error import DomainError
from app.domain.errors.duplicate_idempotency_key_error import DuplicateIdempotencyKeyError
from app.domain.errors.llm_configuration_error import LLMConfigurationError
from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.llm_unavailable_error import LLMUnavailableError
from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.domain.errors.tools_unavailable_error import ToolsUnavailableError
from app.schemas.api.error_response import ErrorResponse
from app.schemas.api.tool_call_public import ToolCallPublic

logger = logging.getLogger(__name__)


class DomainErrorHandler:
    """Único ponto de tradução erro de domínio -> HTTP."""

    STATUS_BY_ERROR: ClassVar[dict[type[DomainError], int]] = {
        RequisitionNotFulfillableError: 422,
        DuplicateIdempotencyKeyError: 409,
        LLMUnavailableError: 502,
        LLMConfigurationError: 502,
        AgentOutputError: 502,
        AgentIterationLimitError: 502,
        ToolsUnavailableError: 503,
        CatalogUnavailableError: 503,
        LLMTimeoutError: 504,
    }
    DEFAULT_STATUS: ClassVar[int] = 500

    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(DomainError, self.handle)

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, DomainError):
            raise exc
        status = self.STATUS_BY_ERROR.get(type(exc), self.DEFAULT_STATUS)
        logger.warning(
            "domain_error error=%s status=%d detail=%s", type(exc).__name__, status, exc.detail
        )
        return JSONResponse(status_code=status, content=self._body(exc).model_dump(mode="json"))

    @staticmethod
    def _body(exc: DomainError) -> ErrorResponse:
        if isinstance(exc, RequisitionNotFulfillableError):
            return ErrorResponse(
                detail=exc.agent_message,
                missing=list(exc.missing),
                tool_calls=[ToolCallPublic.from_domain(trace) for trace in exc.tool_calls],
            )
        return ErrorResponse(detail=exc.user_message)
