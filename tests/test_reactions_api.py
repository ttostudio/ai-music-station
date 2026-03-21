"""リアクションAPI のテスト"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from api.db import get_session
from api.main import app
from worker.models import Track


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def test_client(mock_session):
    async def override_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_track():
    return Track(
        id=uuid.uuid4(),
        channel_id=uuid.uuid4(),
        file_path="/audio/test.wav",
        caption="chill lo-fi beat",
        like_count=0,
        play_count=0,
        created_at=datetime.now(timezone.utc),
    )


class TestAddReaction:
    def test_adds_reaction_successfully(
        self, test_client, mock_session, sample_track,
    ):
        mock_session.get = AsyncMock(return_value=sample_track)
        mock_session.flush = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())
        mock_session.commit = AsyncMock()

        response = test_client.post(
            f"/api/tracks/{sample_track.id}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_returns_409_on_duplicate(
        self, test_client, mock_session, sample_track,
    ):
        mock_session.get = AsyncMock(return_value=sample_track)
        mock_session.flush = AsyncMock(
            side_effect=IntegrityError("dup", params=None, orig=Exception())
        )
        mock_session.rollback = AsyncMock()

        response = test_client.post(
            f"/api/tracks/{sample_track.id}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 409

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.post(
            f"/api/tracks/{uuid.uuid4()}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 404

    def test_rejects_invalid_reaction_type(
        self, test_client, mock_session, sample_track,
    ):
        response = test_client.post(
            f"/api/tracks/{sample_track.id}/reactions",
            json={"session_id": "user-abc", "reaction_type": "dislike"},
        )
        assert response.status_code == 422


class TestRemoveReaction:
    def test_removes_reaction_successfully(
        self, test_client, mock_session, sample_track,
    ):
        sample_track.like_count = 1
        mock_session.get = AsyncMock(return_value=sample_track)

        delete_result = MagicMock()
        delete_result.rowcount = 1
        update_result = MagicMock()
        mock_session.execute = AsyncMock(
            side_effect=[delete_result, update_result]
        )

        response = test_client.request(
            "DELETE",
            f"/api/tracks/{sample_track.id}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_returns_404_when_no_reaction(
        self, test_client, mock_session, sample_track,
    ):
        mock_session.get = AsyncMock(return_value=sample_track)

        delete_result = MagicMock()
        delete_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=delete_result)

        response = test_client.request(
            "DELETE",
            f"/api/tracks/{sample_track.id}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 404

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.request(
            "DELETE",
            f"/api/tracks/{uuid.uuid4()}/reactions",
            json={"session_id": "user-abc", "reaction_type": "like"},
        )
        assert response.status_code == 404


class TestGetReactionStatus:
    def test_returns_status_with_user_reacted(
        self, test_client, mock_session, sample_track,
    ):
        sample_track.like_count = 3
        mock_session.get = AsyncMock(return_value=sample_track)

        count_result = MagicMock()
        count_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=count_result)

        response = test_client.get(
            f"/api/tracks/{sample_track.id}/reactions?session_id=user-abc",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert data["user_reacted"] is True

    def test_returns_status_without_user_reacted(
        self, test_client, mock_session, sample_track,
    ):
        sample_track.like_count = 5
        mock_session.get = AsyncMock(return_value=sample_track)

        count_result = MagicMock()
        count_result.scalar.return_value = 0
        mock_session.execute = AsyncMock(return_value=count_result)

        response = test_client.get(
            f"/api/tracks/{sample_track.id}/reactions?session_id=user-xyz",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert data["user_reacted"] is False

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.get(
            f"/api/tracks/{uuid.uuid4()}/reactions?session_id=user-abc",
        )
        assert response.status_code == 404
