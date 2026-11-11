from pydantic import BaseModel, ConfigDict


class EvalResult(BaseModel):
    """Resultado de um caso: acertou ou não, e por quê."""

    model_config = ConfigDict(frozen=True)

    name: str
    status_code: int
    duration_s: float
    reasons: tuple[str, ...] = ()

    # O caso passa quando não há nenhum motivo de falha.
    @property
    def passed(self) -> bool:
        return not self.reasons
