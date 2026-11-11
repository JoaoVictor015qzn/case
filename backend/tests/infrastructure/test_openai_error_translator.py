import httpx2
import openai

from app.domain.errors.llm_configuration_error import LLMConfigurationError
from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.llm_unavailable_error import LLMUnavailableError
from app.infrastructure.llm.openai_error_translator import OpenAIErrorTranslator

REQUEST = httpx2.Request("POST", "https://openrouter.test/api/v1/responses")
translator = OpenAIErrorTranslator()


class StatusErrors:
    @staticmethod
    def with_status(status: int) -> openai.APIStatusError:
        response = httpx2.Response(status, request=REQUEST)
        return openai.APIStatusError("erro", response=response, body=None)


def test_timeout_becomes_llm_timeout() -> None:
    assert isinstance(translator.translate(openai.APITimeoutError(REQUEST)), LLMTimeoutError)


def test_connection_error_becomes_llm_unavailable() -> None:
    error = openai.APIConnectionError(request=REQUEST)

    assert isinstance(translator.translate(error), LLMUnavailableError)


def test_key_credits_and_model_problems_become_configuration_errors() -> None:
    for status in (400, 401, 402, 404):
        translated = translator.translate(StatusErrors.with_status(status))

        assert isinstance(translated, LLMConfigurationError), status


def test_server_errors_and_rate_limit_become_llm_unavailable() -> None:
    for status in (429, 502, 503):
        assert isinstance(
            translator.translate(StatusErrors.with_status(status)), LLMUnavailableError
        )
