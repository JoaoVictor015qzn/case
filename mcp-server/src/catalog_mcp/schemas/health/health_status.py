from typing import Literal

from pydantic import BaseModel, ConfigDict


# Corpo da resposta de GET /health; sempre {"status": "ok"} quando o servidor está de pé.
class HealthStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
