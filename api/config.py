from __future__ import annotations

from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://app:changeme@localhost:5432/ai_music_station"
    )
    debug: bool = False

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = APISettings()
