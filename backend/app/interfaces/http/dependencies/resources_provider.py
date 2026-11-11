from typing import Annotated

from fastapi import Depends, Request

from app.interfaces.http.dependencies.application_resources import ApplicationResources


# Entrega aos endpoints os recursos guardados em app.state pelo lifespan.
class ResourcesProvider:
    # Atributo de app.state onde o lifespan guarda os ApplicationResources.
    STATE_KEY = "resources"

    # Lê os recursos do app.state; falha se o lifespan não os tiver criado.
    @classmethod
    def get(cls, request: Request) -> ApplicationResources:
        resources = getattr(request.app.state, cls.STATE_KEY, None)
        if not isinstance(resources, ApplicationResources):
            raise RuntimeError("Recursos da aplicação não inicializados (lifespan não rodou).")
        return resources


# Tipo anotado para injetar os recursos nos endpoints via Depends.
ResourcesDep = Annotated[ApplicationResources, Depends(ResourcesProvider.get)]
