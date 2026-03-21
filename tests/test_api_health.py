from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Health endpoint should return 200 even without real DB."""
    with patch("api.routers.health.get_session") as mock_dep:
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 3))

        async def fake_session():
            yield session

        mock_dep.return_value = fake_session()
        app.dependency_overrides[
            __import__("api.db", fromlist=["get_session"]).get_session
        ] = fake_session

        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("正常", "低下")

    app.dependency_overrides.clear()
