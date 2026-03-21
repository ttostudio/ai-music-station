from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app


def test_health_endpoint():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 3
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "正常"
    assert data["database"] == "接続済み"
    assert data["channels_active"] == 3

    app.dependency_overrides.clear()
