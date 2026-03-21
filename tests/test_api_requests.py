from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import Channel, Request


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


@pytest.fixture
def lofi_channel():
    return Channel(
        id=uuid.uuid4(),
        slug="lofi",
        name="LoFi Beats",
        description="Chill beats",
        is_active=True,
        default_bpm_min=70,
        default_bpm_max=90,
        default_duration=180,
        default_instrumental=True,
        prompt_template="lo-fi hip hop",
    )


class TestCreateRequest:
    def test_creates_request(self, test_client, mock_session, lofi_channel):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = lofi_channel

        pos_result = MagicMock()
        pos_result.scalar.return_value = 1

        mock_session.execute = AsyncMock(
            side_effect=[channel_result, pos_result]
        )

        now = datetime.now(timezone.utc)

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.status = "pending"
            obj.created_at = now

        mock_session.refresh = fake_refresh
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        response = test_client.post(
            "/api/channels/lofi/requests",
            json={"caption": "rainy day vibes", "bpm": 80},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["channel_slug"] == "lofi"
        assert data["position"] == 1

    def test_returns_404_for_unknown_channel(
        self, test_client, mock_session,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=channel_result)

        response = test_client.post(
            "/api/channels/nonexistent/requests",
            json={"caption": "test"},
        )
        assert response.status_code == 404

    def test_validates_bpm_range(self, test_client, mock_session):
        response = test_client.post(
            "/api/channels/lofi/requests",
            json={"bpm": 999},
        )
        assert response.status_code == 422


class TestGetRequest:
    def test_returns_404_for_unknown(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.get(f"/api/requests/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_returns_request_detail(
        self, test_client, mock_session, lofi_channel,
    ):
        req_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        req = Request(
            id=req_id,
            channel_id=lofi_channel.id,
            status="pending",
            caption="test",
            created_at=now,
            updated_at=now,
        )

        mock_session.get = AsyncMock(return_value=req)

        channel_result = MagicMock()
        channel_result.scalar_one.return_value = lofi_channel

        pos_result = MagicMock()
        pos_result.scalar.return_value = 1

        mock_session.execute = AsyncMock(
            side_effect=[channel_result, pos_result]
        )

        response = test_client.get(f"/api/requests/{req_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["position"] == 1
