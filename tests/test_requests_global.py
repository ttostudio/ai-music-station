"""
Phase 2 ユニットテスト — GET /api/requests（全チャンネル横断リクエスト一覧）
テストID: UT-BE-020〜023
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import Channel, Request


# ---------------------------------------------------------------------------
# 共通フィクスチャ
# ---------------------------------------------------------------------------

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


def _make_channel(slug: str = "lofi") -> Channel:
    return Channel(
        id=uuid.uuid4(),
        slug=slug,
        name=slug.upper(),
        description="",
        is_active=True,
        default_bpm_min=70,
        default_bpm_max=90,
        default_duration=180,
        default_instrumental=True,
        prompt_template="",
    )


def _make_request(channel: Channel, status: str = "pending") -> Request:
    return Request(
        id=uuid.uuid4(),
        channel_id=channel.id,
        status=status,
        caption=f"test caption - {status}",
        created_at=datetime.now(timezone.utc),
    )


def _mock_list_result(mock_session, request_channel_pairs):
    """list_all_requests の execute を 2 回分（count + rows）モック"""
    count_result = MagicMock()
    count_result.scalar.return_value = len(request_channel_pairs)

    rows_result = MagicMock()
    rows_result.all.return_value = request_channel_pairs

    mock_session.execute = AsyncMock(side_effect=[count_result, rows_result])


# ---------------------------------------------------------------------------
# UT-BE-020〜023: GET /api/requests
# ---------------------------------------------------------------------------

class TestListAllRequests:
    """UT-BE-020〜023: 全チャンネル横断リクエスト一覧エンドポイント"""

    def test_get_all_requests_returns_200(self, test_client, mock_session):
        """UT-BE-020: GET /api/requests → 200 + requests フィールド"""
        ch = _make_channel("lofi")
        req = _make_request(ch, "pending")
        _mock_list_result(mock_session, [(req, ch)])

        response = test_client.get("/api/requests")
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data

    def test_get_requests_filter_by_status(self, test_client, mock_session):
        """UT-BE-021: status=pending → pending のみ返る"""
        ch = _make_channel("lofi")
        pending_req = _make_request(ch, "pending")
        _mock_list_result(mock_session, [(pending_req, ch)])

        response = test_client.get("/api/requests?status=pending")
        assert response.status_code == 200
        data = response.json()
        for req in data["requests"]:
            assert req["status"] == "pending"

    def test_get_requests_empty(self, test_client, mock_session):
        """UT-BE-022: 空のキュー → requests が空配列"""
        _mock_list_result(mock_session, [])
        response = test_client.get("/api/requests")
        assert response.status_code == 200
        assert response.json()["requests"] == []

    def test_get_requests_has_total_field(self, test_client, mock_session):
        """UT-BE-023: レスポンスに total フィールドが含まれる"""
        ch = _make_channel("lofi")
        req = _make_request(ch)
        _mock_list_result(mock_session, [(req, ch)])

        response = test_client.get("/api/requests")
        data = response.json()
        assert "total" in data

    def test_get_requests_multiple_channels(self, test_client, mock_session):
        """UT-BE-020b: 複数チャンネルのリクエストが含まれる"""
        ch1 = _make_channel("lofi")
        ch2 = _make_channel("anime")
        req1 = _make_request(ch1, "pending")
        req2 = _make_request(ch2, "processing")
        _mock_list_result(mock_session, [(req1, ch1), (req2, ch2)])

        response = test_client.get("/api/requests")
        assert response.status_code == 200
        data = response.json()
        slugs = {r["channel_slug"] for r in data["requests"]}
        assert "lofi" in slugs
        assert "anime" in slugs

    def test_get_requests_invalid_status_returns_all(self, test_client, mock_session):
        """UT-BE-020c: 無効な status 値は全件返却（実装が VALID_STATUSES でフィルタリング）"""
        ch = _make_channel("lofi")
        req = _make_request(ch, "pending")
        _mock_list_result(mock_session, [(req, ch)])

        # 無効なステータス値を渡す → 実装が全件フォールバック
        response = test_client.get("/api/requests?status=invalid")
        assert response.status_code == 200

    def test_get_requests_limit_param(self, test_client, mock_session):
        """UT-BE-020d: limit パラメータが受け付けられる"""
        _mock_list_result(mock_session, [])
        response = test_client.get("/api/requests?limit=10")
        assert response.status_code == 200

    def test_get_requests_offset_param(self, test_client, mock_session):
        """UT-BE-020e: offset パラメータが受け付けられる"""
        _mock_list_result(mock_session, [])
        response = test_client.get("/api/requests?offset=10")
        assert response.status_code == 200
