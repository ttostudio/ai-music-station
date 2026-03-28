"""
結合テスト共通フィクスチャ
実 PostgreSQL に接続（product-ai-music-station-postgres-1 の test_music_station DB）
"""
from __future__ import annotations

import uuid
import subprocess
import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from api.db import get_session
from api.main import app
from worker.models import Channel, Track, Request

# テスト用 DB URL（localhost:5433 = docker compose postgres container）
TEST_DATABASE_URL = "postgresql+asyncpg://app:changeme@localhost:5433/test_music_station"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionFactory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


def _run_sql(sql: str) -> str:
    """Docker exec 経由で psql を実行（DDL/DML専用）"""
    result = subprocess.run(
        ["docker", "exec", "product-ai-music-station-postgres-1",
         "psql", "-U", "app", "-d", "test_music_station", "-t", "-c", sql],
        capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture(scope="function")
def test_client() -> Generator:
    """実 DB（test_music_station）に接続した TestClient。
    バックグラウンドワーカーはテスト中は無効化する（ポート5432への接続を避けるため）。
    """
    from unittest.mock import AsyncMock, patch

    async def override_session():
        async with TestSessionFactory() as s:
            yield s

    app.dependency_overrides[get_session] = override_session
    with patch("api.main.start_worker", new=AsyncMock()):
        with patch("api.main.stop_worker", new=AsyncMock()):
            with TestClient(app) as client:
                yield client
    app.dependency_overrides.clear()


def insert_test_channel(slug: str) -> dict:
    """Docker exec psql でテスト用チャンネルを INSERT"""
    ch_id = str(uuid.uuid4())
    # 既存チェック
    existing = _run_sql(f"SELECT id FROM channels WHERE slug = '{slug}' LIMIT 1;")
    if existing:
        return {"id": existing.strip(), "slug": slug}

    _run_sql(f"""
        INSERT INTO channels (id, slug, name, description, is_active,
            default_bpm_min, default_bpm_max, default_duration, default_instrumental,
            prompt_template, created_at, updated_at)
        VALUES ('{ch_id}', '{slug}', 'Test {slug}', 'Integration test', true,
            70, 90, 180, true, 'test', NOW(), NOW())
        ON CONFLICT (slug) DO NOTHING;
    """)
    existing = _run_sql(f"SELECT id FROM channels WHERE slug = '{slug}' LIMIT 1;")
    return {"id": existing.strip(), "slug": slug}


def insert_test_track(title: str, mood: str = "chill", play_count: int = 0,
                      channel_slug: str = "test-integration") -> dict:
    """Docker exec psql でテスト用トラックを INSERT"""
    ch = insert_test_channel(channel_slug)
    track_id = str(uuid.uuid4())
    _run_sql(f"""
        INSERT INTO tracks (id, channel_id, file_path, caption, title, mood, duration_ms,
            play_count, like_count, is_retired, created_at)
        VALUES ('{track_id}', '{ch["id"]}', '/tracks/test.mp3',
            '{title} caption', '{title}', '{mood}', 180000,
            {play_count}, 0, false, NOW());
    """)
    return {"id": track_id, "title": title, "channel_slug": channel_slug}


def insert_test_request(status: str = "pending", channel_slug: str = "test-integration") -> dict:
    """Docker exec psql でテスト用リクエストを INSERT"""
    ch = insert_test_channel(channel_slug)
    req_id = str(uuid.uuid4())
    _run_sql(f"""
        INSERT INTO requests (id, channel_id, status, caption, created_at)
        VALUES ('{req_id}', '{ch["id"]}', '{status}',
            'integration test request - {status}', NOW());
    """)
    return {"id": req_id, "status": status, "channel_slug": channel_slug}
