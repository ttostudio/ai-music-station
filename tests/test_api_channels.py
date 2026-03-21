from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import Channel


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


class TestListChannels:
    def test_returns_empty_list(self, test_client, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.get("/api/channels")
        assert response.status_code == 200
        data = response.json()
        assert data["channels"] == []

    def test_returns_channels(self, test_client, mock_session, lofi_channel):
        # First call: channel list query
        channel_result = MagicMock()
        channel_result.scalars.return_value.all.return_value = [lofi_channel]

        # Subsequent calls for counts and now_playing
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        np_result = MagicMock()
        np_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[channel_result, count_result, count_result, np_result]
        )

        response = test_client.get("/api/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data["channels"]) == 1
        assert data["channels"][0]["slug"] == "lofi"
        assert data["channels"][0]["stream_url"] == "/stream/lofi.ogg"


class TestGetChannel:
    def test_returns_404_for_unknown(self, test_client, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.get("/api/channels/nonexistent")
        assert response.status_code == 404

    def test_returns_channel_detail(
        self, test_client, mock_session, lofi_channel,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = lofi_channel

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        np_result = MagicMock()
        np_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[
                channel_result, count_result, count_result, np_result,
            ]
        )

        response = test_client.get("/api/channels/lofi")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "lofi"
        assert data["default_bpm_min"] == 70
        assert data["default_bpm_max"] == 90
