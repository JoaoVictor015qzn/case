import sys
import time
import uuid

import httpx

from evals.catalog_reference import CatalogReference
from evals.eval_case import EvalCase
from evals.eval_cases import EvalCases
from evals.eval_checker import EvalChecker
from evals.eval_result import EvalResult
from evals.eval_settings import EvalSettings


class EvalRunner:
    """Envia cada pedido ao sistema no ar e imprime o placar. Sai com código 1 abaixo do mínimo."""

    # Content-type que indica corpo JSON na resposta.
    JSON = "application/json"

    # Recebe configuração, cliente HTTP do backend e o verificador de acertos.
    def __init__(self, settings: EvalSettings, api: httpx.Client, checker: EvalChecker) -> None:
        self._settings = settings
        self._api = api
        self._checker = checker

    # Roda todos os casos, imprime o placar e devolve o código de saída.
    def run(self, cases: tuple[EvalCase, ...]) -> int:
        results = [self._run_case(case) for case in cases]
        for result in results:
            self._write(result)
        # Placar final: 0 se atingiu o mínimo de acertos, 1 caso contrário.
        passed = sum(result.passed for result in results)
        self._write_line(f"\n{passed}/{len(results)} acertos ({passed / len(results):.0%})")
        return 0 if passed >= self._settings.min_passed else 1

    # Envia um pedido ao POST /requisicoes, mede o tempo e confere a resposta.
    def _run_case(self, case: EvalCase) -> EvalResult:
        started = time.perf_counter()
        # Chave de idempotência nova a cada execução para não reaproveitar requisições antigas.
        try:
            response = self._api.post(
                "/requisicoes",
                json={"requestText": case.request_text},
                headers={"Idempotency-Key": f"eval-{uuid.uuid4().hex}"},
            )
        # Sistema fora do ar ou timeout conta como falha com status 0.
        except httpx.HTTPError as exc:
            return EvalResult(
                name=case.name,
                status_code=0,
                duration_s=round(time.perf_counter() - started, 1),
                reasons=(f"sem resposta do sistema: {exc!r}",),
            )
        # Só decodifica o corpo se for JSON; senão confere com corpo vazio.
        body = response.json() if self.JSON in response.headers.get("content-type", "") else {}
        reasons = self._checker.check(case, response.status_code, body)
        return EvalResult(
            name=case.name,
            status_code=response.status_code,
            duration_s=round(time.perf_counter() - started, 1),
            reasons=tuple(reasons),
        )

    # Imprime a linha do caso (OK/FALHA, status, duração) e os motivos de falha.
    def _write(self, result: EvalResult) -> None:
        mark = "OK  " if result.passed else "FALHA"
        self._write_line(
            f"{mark} {result.name:<30} HTTP {result.status_code}  {result.duration_s:>5}s"
        )
        for reason in result.reasons:
            self._write_line(f"      - {reason}")

    # Escreve no stdout e força o flush para o progresso aparecer na hora.
    @staticmethod
    def _write_line(text: str) -> None:
        sys.stdout.write(f"{text}\n")
        sys.stdout.flush()

    # Monta os clientes do backend e da DummyJSON e roda os casos de EvalCases.ALL.
    @classmethod
    def main(cls) -> int:
        settings = EvalSettings()
        with (
            httpx.Client(base_url=settings.base_url, timeout=settings.timeout_s) as api,
            httpx.Client(base_url=settings.catalog_url, timeout=10) as catalog,
        ):
            checker = EvalChecker(CatalogReference(catalog))
            return cls(settings, api, checker).run(EvalCases.ALL)


if __name__ == "__main__":
    sys.exit(EvalRunner.main())
