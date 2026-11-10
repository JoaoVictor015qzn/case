from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

from catalog_mcp.schemas.health.health_status import HealthStatus


class HealthRoute:
    PATH = "/health"

    def register(self, server: MCPServer) -> None:
        server.custom_route(self.PATH, methods=["GET"])(self.handle)

    async def handle(self, _request: Request) -> JSONResponse:
        return JSONResponse(HealthStatus().model_dump())
