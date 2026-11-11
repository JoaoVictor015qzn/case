import logging

import openai

from app.domain.errors.domain_error import DomainError
from app.domain.errors.llm_configuration_error import LLMConfigurationError
from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.llm_unavailable_error import LLMUnavailableError

logger = logging.getLogger(__name__)


class OpenAIErrorTranslator:
    """Exceções do SDK openai (falando com a OpenRouter) -> erros de domínio."""

    # 400 schema/parâmetro recusado, 401 chave, 402 sem créditos, 403 bloqueio, 404 modelo.
    CONFIGURATION_STATUSES = frozenset({400, 401, 402, 403, 404})

    # Classifica o erro do SDK em timeout, configuração ou indisponibilidade do LLM.
    def translate(self, error: openai.OpenAIError) -> DomainError:
        if isinstance(error, openai.APITimeoutError):
            return LLMTimeoutError(str(error))
        # Status de configuração (chave, créditos, modelo) é logado com dica de correção.
        if (
            isinstance(error, openai.APIStatusError)
            and error.status_code in self.CONFIGURATION_STATUSES
        ):
            logger.error(
                "llm_configuration status=%d message=%s "
                "(verifique OPENROUTER_API_KEY, créditos e OPENROUTER_MODEL)",
                error.status_code,
                error.message,
            )
            return LLMConfigurationError(f"status={error.status_code} {error.message}")
        # Qualquer outra falha (rede, 5xx, rate limit) vira indisponibilidade.
        return LLMUnavailableError(f"{type(error).__name__}: {error}")
