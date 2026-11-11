from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.schemas.settings.settings import Settings


# Fornece as Settings lidas do ambiente para injeção via Depends.
class SettingsProvider:
    # Lê as Settings uma única vez e reaproveita o resultado em cache.
    @staticmethod
    @lru_cache
    def get() -> Settings:
        return Settings()


# Tipo anotado para injetar as Settings nos endpoints e providers.
SettingsDep = Annotated[Settings, Depends(SettingsProvider.get)]
