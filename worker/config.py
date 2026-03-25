from __future__ import annotations

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:changeme@localhost:5432/ai_music_station"
    # ACE-Step API の URL（コンテナ内から host.docker.internal 経由でアクセス）
    acestep_api_url: str = "http://host.docker.internal:8001"
    acestep_timeout: int = 300  # 5 minutes
    acestep_retries: int = 3
    # ポーリング設定
    acestep_poll_interval: float = 5.0   # 秒（ACE-Step 推奨）
    acestep_max_poll_count: int = 720    # 最大ポーリング回数（5s × 720 = 60分）
    poll_interval: float = 2.0  # Worker の次リクエスト確認間隔
    heartbeat_interval: float = 30.0  # seconds
    generated_tracks_dir: str = "./generated_tracks"
    liquidsoap_tracks_dir: str = "/tracks"  # Liquidsoap コンテナ内パス
    worker_id: str = ""
    claude_command: str = "claude"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = WorkerSettings()
