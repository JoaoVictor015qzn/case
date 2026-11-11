from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

from catalog_mcp.schemas.health.health_status import HealthStatus


# Rota HTTP de health check usada pelo healthcheck do Docker Compose.
class HealthRoute:
    PATH = "/health"

    # Registra GET /health como rota customizada do servidor MCP.
    def register(self, server: MCPServer) -> None:
        server.custom_route(self.PATH, methods=["GET"])(self.handle)

    # Responde com o status fixo de saúde em JSON.
    async def handle(self, _request: Request) -> JSONResponse:
        return JSONResponse(HealthStatus().model_dump())
