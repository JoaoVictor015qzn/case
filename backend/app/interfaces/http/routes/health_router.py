from fastapi import APIRouter

from app.schemas.health.health_status import HealthStatus


class HealthRouter:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/health", tags=["health"])
        self.router.add_api_route("", self.check, methods=["GET"])

    def check(self) -> HealthStatus:
        return HealthStatus()
