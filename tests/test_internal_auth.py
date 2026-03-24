from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def test_client(mock_session):
    async def override_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestInternalAPIAuth:
    """POST /internal/* エンドポイントの認証テスト"""

    def test_now_playing_without_auth_header_returns_401(self, test_client: TestClient):
        """Authorization ヘッダーなしで 401 を返すこと"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/now-playing",
                json={"channel_slug": "lofi", "track_id": "00000000-0000-0000-0000-000000000001"},
            )
        assert response.status_code == 401

    def test_now_playing_with_wrong_key_returns_401(self, test_client: TestClient):
        """不正なAPIキーで 401 を返すこと"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/now-playing",
                json={"channel_slug": "lofi", "track_id": "00000000-0000-0000-0000-000000000001"},
                headers={"Authorization": "Bearer wrongkey"},
            )
        assert response.status_code == 401

    def test_now_playing_with_valid_key_passes_auth(self, test_client: TestClient, mock_session: AsyncMock):
        """正しいAPIキーで認証が通ること"""
        channel_mock = MagicMock()
        channel_mock.id = "00000000-0000-0000-0000-000000000010"
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = channel_mock

        np_mock = MagicMock()
        np_mock.track_id = None
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.get = AsyncMock(return_value=np_mock)
        mock_session.commit = AsyncMock()

        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/now-playing",
                json={"channel_slug": "lofi", "track_id": "00000000-0000-0000-0000-000000000001"},
                headers={"Authorization": "Bearer secret123"},
            )
        # 認証は通過しているので 4xx 認証エラーではないこと
        assert response.status_code != 401

    def test_now_playing_without_env_key_returns_401(self, test_client: TestClient):
        """INTERNAL_API_KEY 未設定の場合は 401 を返すこと"""
        env = {k: v for k, v in os.environ.items() if k != "INTERNAL_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            response = test_client.post(
                "/internal/now-playing",
                json={"channel_slug": "lofi", "track_id": "00000000-0000-0000-0000-000000000001"},
                headers={"Authorization": "Bearer secret123"},
            )
        assert response.status_code == 401

    def test_worker_heartbeat_without_auth_returns_401(self, test_client: TestClient):
        """worker-heartbeat も認証が必要なこと"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/worker-heartbeat",
                json={"worker_id": "worker-001"},
            )
        assert response.status_code == 401

    def test_worker_heartbeat_with_valid_key_returns_200(self, test_client: TestClient):
        """worker-heartbeat が正しいキーで通過すること"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/worker-heartbeat",
                json={"worker_id": "worker-001"},
                headers={"Authorization": "Bearer secret123"},
            )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_bearer_scheme_case_insensitive(self, test_client: TestClient):
        """Bearer スキームは大文字小文字を区別しないこと"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/worker-heartbeat",
                json={"worker_id": "worker-001"},
                headers={"Authorization": "BEARER secret123"},
            )
        assert response.status_code == 200

    def test_invalid_scheme_returns_401(self, test_client: TestClient):
        """Basic 認証スキームで 401 を返すこと"""
        with patch.dict(os.environ, {"INTERNAL_API_KEY": "secret123"}):
            response = test_client.post(
                "/internal/worker-heartbeat",
                json={"worker_id": "worker-001"},
                headers={"Authorization": "Basic dXNlcjpwYXNz"},
            )
        assert response.status_code == 401
