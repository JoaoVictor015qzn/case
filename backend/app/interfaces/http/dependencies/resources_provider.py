from typing import Annotated

from fastapi import Depends, Request

from app.interfaces.http.dependencies.application_resources import ApplicationResources


class ResourcesProvider:
    STATE_KEY = "resources"

    @classmethod
    def get(cls, request: Request) -> ApplicationResources:
        resources = getattr(request.app.state, cls.STATE_KEY, None)
        if not isinstance(resources, ApplicationResources):
            raise RuntimeError("Recursos da aplicação não inicializados (lifespan não rodou).")
        return resources


ResourcesDep = Annotated[ApplicationResources, Depends(ResourcesProvider.get)]
