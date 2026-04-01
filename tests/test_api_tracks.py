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
        min_duration=180,
        max_duration=600,
        default_instrumental=True,
        prompt_template="lo-fi hip hop",
    )


class TestListTracks:
    def test_returns_404_for_unknown_channel(
        self, test_client, mock_session,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=channel_result)

        response = test_client.get("/api/channels/nonexistent/tracks")
        assert response.status_code == 404

    def test_returns_empty_tracks(
        self, test_client, mock_session, lofi_channel,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = lofi_channel

        tracks_result = MagicMock()
        tracks_result.scalars.return_value.all.return_value = []

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        mock_session.execute = AsyncMock(
            side_effect=[channel_result, tracks_result, count_result]
        )

        response = test_client.get("/api/channels/lofi/tracks")
        assert response.status_code == 200
        data = response.json()
        assert data["tracks"] == []
        assert data["total"] == 0


class TestNowPlaying:
    def test_returns_null_when_nothing_playing(
        self, test_client, mock_session, lofi_channel,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = lofi_channel

        np_result = MagicMock()
        np_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[channel_result, np_result]
        )

        response = test_client.get("/api/channels/lofi/now-playing")
        assert response.status_code == 200
        data = response.json()
        assert data["track"] is None

    def test_returns_404_for_unknown_channel(
        self, test_client, mock_session,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=channel_result)

        response = test_client.get("/api/channels/unknown/now-playing")
        assert response.status_code == 404
