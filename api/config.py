from __future__ import annotations

from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://app:changeme@localhost:5432/ai_music_station"
    )
    debug: bool = False
    claude_command: str = "claude"
    public_base_url: str = "http://localhost:3200"
    analytics_ip_salt: str = "changeme-random-salt"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = APISettings()
