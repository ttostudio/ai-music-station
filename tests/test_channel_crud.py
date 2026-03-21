from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import Channel, NowPlaying


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
def create_body():
    return {
        "slug": "electronic",
        "name": "エレクトロニカ",
        "description": "電子音楽チャンネル",
        "prompt_template": "electronic ambient music",
        "default_bpm_min": 100,
        "default_bpm_max": 140,
        "default_duration": 200,
    }


@pytest.fixture
def existing_channel():
    return Channel(
        id=uuid.uuid4(),
        slug="electronic",
        name="エレクトロニカ",
        description="電子音楽チャンネル",
        is_active=True,
        default_bpm_min=100,
        default_bpm_max=140,
        default_duration=200,
        default_instrumental=True,
        prompt_template="electronic ambient music",
        auto_generate=True,
        min_stock=5,
        max_stock=50,
    )


class TestCreateChannel:
    def test_creates_channel(self, test_client, mock_session, create_body):
        # No existing channel with this slug
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        # refresh populates DB defaults (id, is_active)
        async def fake_refresh(obj):
            if obj.id is None:
                obj.id = uuid.uuid4()
            if obj.is_active is None:
                obj.is_active = True

        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        response = test_client.post("/api/channels", json=create_body)
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "electronic"
        assert data["name"] == "エレクトロニカ"
        mock_session.add.assert_called_once()

    def test_rejects_duplicate_slug(
        self, test_client, mock_session, create_body, existing_channel,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_channel
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.post("/api/channels", json=create_body)
        assert response.status_code == 409

    def test_rejects_invalid_slug(self, test_client, mock_session, create_body):
        create_body["slug"] = "Invalid Slug!"
        response = test_client.post("/api/channels", json=create_body)
        assert response.status_code == 422

    def test_rejects_missing_name(self, test_client, mock_session, create_body):
        del create_body["name"]
        response = test_client.post("/api/channels", json=create_body)
        assert response.status_code == 422

    def test_rejects_missing_prompt_template(
        self, test_client, mock_session, create_body,
    ):
        del create_body["prompt_template"]
        response = test_client.post("/api/channels", json=create_body)
        assert response.status_code == 422


class TestUpdateChannel:
    def test_updates_channel(
        self, test_client, mock_session, create_body, existing_channel,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_channel
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        create_body["name"] = "更新後の名前"
        response = test_client.put(
            "/api/channels/electronic", json=create_body,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新後の名前"

    def test_returns_404_for_unknown(
        self, test_client, mock_session, create_body,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.put(
            "/api/channels/nonexistent", json=create_body,
        )
        assert response.status_code == 404


class TestDeleteChannel:
    def test_deletes_channel(
        self, test_client, mock_session, existing_channel,
    ):
        # First call: find channel
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = existing_channel

        # Second call: count tracks to retire
        count_result = MagicMock()
        count_result.scalar.return_value = 3

        # Third call: update tracks (retire)
        update_tracks_result = MagicMock()

        # Fourth call: update requests (cancel)
        update_requests_result = MagicMock()

        # Fifth call: find now_playing
        np_result = MagicMock()
        np_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[
                channel_result,
                count_result,
                update_tracks_result,
                update_requests_result,
                np_result,
            ],
        )
        mock_session.commit = AsyncMock()

        response = test_client.delete("/api/channels/electronic")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["deleted_tracks"] == 3
        assert existing_channel.is_active is False

    def test_deletes_now_playing(
        self, test_client, mock_session, existing_channel,
    ):
        channel_result = MagicMock()
        channel_result.scalar_one_or_none.return_value = existing_channel

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        update_tracks_result = MagicMock()
        update_requests_result = MagicMock()

        np = NowPlaying(
            channel_id=existing_channel.id,
            track_id=uuid.uuid4(),
        )
        np_result = MagicMock()
        np_result.scalar_one_or_none.return_value = np

        mock_session.execute = AsyncMock(
            side_effect=[
                channel_result,
                count_result,
                update_tracks_result,
                update_requests_result,
                np_result,
            ],
        )
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        response = test_client.delete("/api/channels/electronic")
        assert response.status_code == 200
        mock_session.delete.assert_called_once_with(np)

    def test_returns_404_for_unknown(self, test_client, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.delete("/api/channels/nonexistent")
        assert response.status_code == 404
