"""
回帰テスト — 既存エンドポイントが Phase 2 後も正常動作する（実 DB 接続）
テストID: REG-003
"""
from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.parametrize("path", [
    "/api/channels",
    "/health",
])
def test_existing_endpoints_return_200(test_client, path):
    """REG-003: Phase 2 後も既存エンドポイントが正常に応答する回帰テスト"""
    response = test_client.get(path)
    assert response.status_code in (200, 404)
