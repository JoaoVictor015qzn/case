from typing import Literal

from pydantic import BaseModel, ConfigDict


# Resposta do healthcheck: o serviço está de pé.
class HealthStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
