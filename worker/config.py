from __future__ import annotations

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:changeme@localhost:5432/ai_music_station"
    acestep_api_url: str = "http://localhost:8001"
    acestep_timeout: int = 300  # 5 minutes
    acestep_retries: int = 3
    poll_interval: float = 2.0  # seconds
    heartbeat_interval: float = 30.0  # seconds
    generated_tracks_dir: str = "./generated_tracks"
    liquidsoap_tracks_dir: str = "/tracks"  # Liquidsoap コンテナ内パス
    worker_id: str = ""
    claude_command: str = "claude"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = WorkerSettings()
