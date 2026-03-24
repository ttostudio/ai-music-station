"""共有リンク API のテスト"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.db import get_session
from api.main import app
from worker.models import Channel, ShareLink, Track


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
        title="Midnight Rain",
        mood="chill",
        like_count=0,
        play_count=0,
        is_retired=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_channel():
    return Channel(
        id=uuid.uuid4(),
        slug="lofi",
        name="Lo-Fi Chill",
        description="Lo-fi beats",
        is_active=True,
        prompt_template="lofi template",
    )


class TestCreateShareLink:
    def test_creates_new_share_link(self, test_client, mock_session, sample_track):
        mock_session.get = AsyncMock(return_value=sample_track)

        # 既存トークンなし
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        response = test_client.post(f"/api/tracks/{sample_track.id}/share")
        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
        assert data["track_id"] == str(sample_track.id)

    def test_returns_existing_token_idempotent(
        self, test_client, mock_session, sample_track
    ):
        mock_session.get = AsyncMock(return_value=sample_track)

        existing_link = ShareLink(
            id=uuid.uuid4(),
            track_id=sample_track.id,
            share_token="existing-token-abc",
            created_at=datetime.now(timezone.utc),
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_link
        mock_session.execute = AsyncMock(return_value=result_mock)

        response = test_client.post(f"/api/tracks/{sample_track.id}/share")
        assert response.status_code == 200
        data = response.json()
        assert data["share_token"] == "existing-token-abc"

    def test_returns_404_for_unknown_track(self, test_client, mock_session):
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.post(f"/api/tracks/{uuid.uuid4()}/share")
        assert response.status_code == 404

    def test_returns_404_for_retired_track(self, test_client, mock_session, sample_track):
        sample_track.is_retired = True
        mock_session.get = AsyncMock(return_value=sample_track)

        response = test_client.post(f"/api/tracks/{sample_track.id}/share")
        assert response.status_code == 404


class TestSharePage:
    def test_returns_ogp_html(self, test_client, mock_session, sample_track, sample_channel):
        link = ShareLink(
            id=uuid.uuid4(),
            track_id=sample_track.id,
            share_token="test-token-xyz",
            created_at=datetime.now(timezone.utc),
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = link

        # session.execute → link, session.get → track then channel
        mock_session.execute = AsyncMock(return_value=result_mock)
        sample_track.channel_id = sample_channel.id
        mock_session.get = AsyncMock(side_effect=[sample_track, sample_channel])
        mock_session.commit = AsyncMock()

        response = test_client.get("/share/test-token-xyz")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        html = response.text
        assert 'og:title' in html
        assert 'og:description' in html
        assert 'og:image' in html
        assert 'twitter:card' in html
        assert "Midnight Rain" in html

    def test_returns_404_for_invalid_token(self, test_client, mock_session):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result_mock)

        response = test_client.get("/share/nonexistent-token")
        assert response.status_code == 404

    def test_returns_404_for_retired_track(
        self, test_client, mock_session, sample_track
    ):
        sample_track.is_retired = True
        link = ShareLink(
            id=uuid.uuid4(),
            track_id=sample_track.id,
            share_token="token-retired",
            created_at=datetime.now(timezone.utc),
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = link
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.get = AsyncMock(return_value=sample_track)

        response = test_client.get("/share/token-retired")
        assert response.status_code == 404

    def test_rejects_overlong_token(self, test_client, mock_session):
        long_token = "a" * 65
        response = test_client.get(f"/share/{long_token}")
        assert response.status_code == 404

    def test_html_escapes_track_title(
        self, test_client, mock_session, sample_track, sample_channel
    ):
        sample_track.title = '<script>alert("xss")</script>'
        link = ShareLink(
            id=uuid.uuid4(),
            track_id=sample_track.id,
            share_token="xss-test-token",
            created_at=datetime.now(timezone.utc),
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = link
        mock_session.execute = AsyncMock(return_value=result_mock)
        sample_track.channel_id = sample_channel.id
        mock_session.get = AsyncMock(side_effect=[sample_track, sample_channel])
        mock_session.commit = AsyncMock()

        response = test_client.get("/share/xss-test-token")
        assert response.status_code == 200
        # OGP title should have the escaped version, not raw script tag
        assert 'content="&lt;script&gt;' in response.text
        assert 'content="<script>' not in response.text
