from fastapi import APIRouter

from app.schemas.health.health_status import HealthStatus


# Router do healthcheck do backend.
class HealthRouter:
    # Registra GET /health.
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/health", tags=["health"])
        self.router.add_api_route("", self.check, methods=["GET"])

    # Responde que o processo está no ar.
    def check(self) -> HealthStatus:
        return HealthStatus()
