import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.interfaces.http.dependencies.application_resources import ApplicationResources
from app.interfaces.http.dependencies.resources_provider import ResourcesProvider
from app.interfaces.http.dependencies.settings_provider import SettingsProvider
from app.interfaces.http.errors.domain_error_handler import DomainErrorHandler
from app.interfaces.http.errors.request_validation_error_handler import (
    RequestValidationErrorHandler,
)
from app.interfaces.http.errors.unexpected_error_handler import UnexpectedErrorHandler
from app.interfaces.http.middleware.correlation_id import CorrelationId
from app.interfaces.http.middleware.correlation_id_middleware import CorrelationIdMiddleware
from app.interfaces.http.routes.health_router import HealthRouter
from app.interfaces.http.routes.requisitions_router import RequisitionsRouter
from app.schemas.settings.settings import Settings


class Application:
    """Composition root: o único lugar que decide qual implementação entra em cada port."""

    LOG_FORMAT = "%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s %(message)s"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self) -> FastAPI:
        self._configure_logging()
        app = FastAPI(
            title="Agente de compras",
            description="Transforma pedidos em texto em requisições de compra.",
            lifespan=self._lifespan,
        )
        app.add_middleware(CorrelationIdMiddleware)
        DomainErrorHandler().register(app)
        RequestValidationErrorHandler().register(app)
        UnexpectedErrorHandler().register(app)
        app.include_router(RequisitionsRouter().router)
        app.include_router(HealthRouter().router)
        return app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncGenerator[None]:
        resources = ApplicationResources.from_settings(self._settings)
        setattr(app.state, ResourcesProvider.STATE_KEY, resources)
        try:
            yield
        finally:
            await resources.close()

    def _configure_logging(self) -> None:
        handler = logging.StreamHandler()
        handler.addFilter(CorrelationId())
        handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        logging.basicConfig(level=self._settings.log_level, handlers=[handler], force=True)


app = Application(SettingsProvider.get()).create()
