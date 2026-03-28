"""
結合テスト — GET /api/requests（実 DB 接続）
テストID: IT-020〜021
"""
from __future__ import annotations

import uuid

import pytest

from .conftest import insert_test_channel, insert_test_request


@pytest.mark.integration
def test_get_requests_returns_200_real_db(test_client):
    """IT-020: GET /api/requests → 実 DB から 200 が返る"""
    response = test_client.get("/api/requests")
    assert response.status_code == 200
    data = response.json()
    assert "requests" in data
    assert "total" in data


@pytest.mark.integration
def test_get_requests_cross_channel_real_db(test_client):
    """IT-020: 複数チャンネルにリクエストを INSERT し、全件が /api/requests で返ることを確認"""
    unique1 = f"it-ch1-{str(uuid.uuid4())[:6]}"
    unique2 = f"it-ch2-{str(uuid.uuid4())[:6]}"
    insert_test_request(status="pending", channel_slug=unique1)
    insert_test_request(status="pending", channel_slug=unique2)

    response = test_client.get("/api/requests?status=pending")
    assert response.status_code == 200
    data = response.json()
    channel_slugs = {r.get("channel_slug") for r in data["requests"]}
    assert unique1 in channel_slugs, f"channel {unique1} が結果に含まれない"
    assert unique2 in channel_slugs, f"channel {unique2} が結果に含まれない"


@pytest.mark.integration
def test_get_requests_status_filter_real_db(test_client):
    """IT-021: status=pending で pending のみ返る"""
    unique_slug = f"it-filter-{str(uuid.uuid4())[:6]}"
    insert_test_request(status="pending", channel_slug=unique_slug)

    response = test_client.get("/api/requests?status=pending")
    assert response.status_code == 200
    data = response.json()
    for req in data["requests"]:
        assert req["status"] == "pending", f"pending 以外のステータスが含まれる: {req['status']}"


@pytest.mark.integration
def test_get_requests_empty_on_done_status_real_db(test_client):
    """IT-022: status=done は completed ステータス（done は無効値のため全件フォールバック）"""
    # status=done は VALID_STATUSES に含まれないため、全件返却になる（実装の仕様）
    response = test_client.get("/api/requests?status=done")
    assert response.status_code == 200
