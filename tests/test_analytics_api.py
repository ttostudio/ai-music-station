"""アナリティクス API のテスト"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import ShareLink, Track


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
        file_path="/audio/test.flac",
        caption="chill lo-fi beat",
        like_count=5,
        play_count=42,
        is_retired=False,
        created_at=datetime.now(timezone.utc),
    )


class TestRecordPlay:
    def test_records_play_event(self, test_client, mock_session, sample_track):
        mock_session.get = AsyncMock(return_value=sample_track)

        # share_token なし → execute は呼ばれない（token検索をスキップ）
        mock_session.commit = AsyncMock()

        response = test_client.post(
            "/api/analytics/play",
            json={"track_id": str(sample_track.id)},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["ok"] is True

    def test_records_play_with_valid_share_token(
        self, test_client, mock_session, sample_track
    ):
        mock_session.get = AsyncMock(return_value=sample_track)

        existing_link = ShareLink(
            id=uuid.uuid4(),
            track_id=sample_track.id,
            share_token="valid-share-token",
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_link
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.commit = AsyncMock()

        response = test_client.post(
            "/api/analytics/play",
            json={
                "track_id": str(sample_track.id),
                "share_token": "valid-share-token",
            },
        )
        assert response.status_code == 202
        assert response.json()["ok"] is True

    def test_records_play_with_invalid_share_token_as_null(
        self, test_client, mock_session, sample_track
    ):
        mock_session.get = AsyncMock(return_value=sample_track)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.commit = AsyncMock()

        response = test_client.post(
            "/api/analytics/play",
            json={
                "track_id": str(sample_track.id),
                "share_token": "nonexistent-token",
            },
        )
        assert response.status_code == 202
        assert response.json()["ok"] is True

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.post(
            "/api/analytics/play",
            json={"track_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    def test_returns_404_for_retired_track(
        self, test_client, mock_session, sample_track
    ):
        sample_track.is_retired = True
        mock_session.get = AsyncMock(return_value=sample_track)

        response = test_client.post(
            "/api/analytics/play",
            json={"track_id": str(sample_track.id)},
        )
        assert response.status_code == 404

    def test_rejects_invalid_share_token_format(self, test_client, mock_session):
        response = test_client.post(
            "/api/analytics/play",
            json={
                "track_id": str(uuid.uuid4()),
                "share_token": "invalid token with spaces!@#",
            },
        )
        assert response.status_code == 422

    def test_returns_202_even_when_db_write_fails(
        self, test_client, mock_session, sample_track
    ):
        mock_session.get = AsyncMock(return_value=sample_track)
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))

        response = test_client.post(
            "/api/analytics/play",
            json={"track_id": str(sample_track.id)},
        )
        assert response.status_code == 202
        assert response.json()["ok"] is True


class TestGetTrackStats:
    def test_returns_stats(self, test_client, mock_session, sample_track):
        mock_session.get = AsyncMock(return_value=sample_track)

        # 3 execute calls: share_count, play_total, share_plays
        share_count_result = MagicMock()
        share_count_result.scalar.return_value = 3

        play_total_result = MagicMock()
        play_total_result.scalar.return_value = 42

        share_play_result = MagicMock()
        share_play_result.scalar.return_value = 10

        mock_session.execute = AsyncMock(
            side_effect=[share_count_result, play_total_result, share_play_result]
        )

        response = test_client.get(
            f"/api/analytics/tracks/{sample_track.id}/stats"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["track_id"] == str(sample_track.id)
        assert data["play_count"] == 42
        assert data["share_count"] == 3
        assert data["like_count"] == 5
        assert data["plays_by_source"]["direct"] == 32
        assert data["plays_by_source"]["share_page"] == 10

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.get(
            f"/api/analytics/tracks/{uuid.uuid4()}/stats"
        )
        assert response.status_code == 404
