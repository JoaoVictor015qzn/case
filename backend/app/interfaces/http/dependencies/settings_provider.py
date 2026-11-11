from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.schemas.settings.settings import Settings


class SettingsProvider:
    @staticmethod
    @lru_cache
    def get() -> Settings:
        return Settings()


SettingsDep = Annotated[Settings, Depends(SettingsProvider.get)]
