"""プレイリストAPI のテスト"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from api.db import get_session
from api.main import app
from worker.models import Playlist, PlaylistTrack, Reaction, Track

SESSION_ID = "session-abc-001"
SESSION_ID_OTHER = "session-xyz-999"


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def test_client(mock_session):
    async def override_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_playlist():
    return Playlist(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        name="テストプレイリスト",
        description="テスト用",
        session_id=SESSION_ID,
        is_public=True,
        created_at=datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_track():
    return Track(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        channel_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        file_path="/audio/test.flac",
        caption="chill beat",
        title="Test Track",
        mood="chill",
        duration_ms=180000,
        bpm=120,
        like_count=0,
        play_count=0,
        is_retired=False,
        quality_score=75.0,
        created_at=datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc),
    )


def _mock_scalar(value):
    """select + scalar() のモックヘルパー"""
    result = MagicMock()
    result.scalar.return_value = value
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_all(items):
    """select + scalars().all() のモックヘルパー"""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = items
    result.scalars.return_value = scalars
    return result


# ========================================
# プレイリスト CRUD
# ========================================

class TestCreatePlaylist:
    """API-001〜API-003"""

    def test_create_playlist_success(self, test_client, mock_session):
        """API-001: 正常作成"""
        # count(プレイリスト数) → 0, count(重複チェック) → 0
        mock_session.execute = AsyncMock(side_effect=[
            _mock_scalar(0),  # playlist count
            _mock_scalar(0),  # dup check
        ])
        mock_session.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, 'id', uuid.uuid4()) or setattr(obj, 'created_at', datetime.now(timezone.utc)) or setattr(obj, 'updated_at', datetime.now(timezone.utc)))

        response = test_client.post(
            "/api/playlists",
            json={"name": "マイリスト", "description": "説明"},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "マイリスト"
        assert data["track_count"] == 0

    def test_create_playlist_no_session_header(self, test_client):
        """セッションIDなしで400"""
        response = test_client.post(
            "/api/playlists",
            json={"name": "テスト"},
        )
        assert response.status_code == 400

    def test_create_playlist_no_name(self, test_client):
        """API-002: 名前なしで422"""
        response = test_client.post(
            "/api/playlists",
            json={"description": "説明のみ"},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 422

    def test_create_playlist_duplicate_name(self, test_client, mock_session):
        """重複名で409"""
        mock_session.execute = AsyncMock(side_effect=[
            _mock_scalar(0),  # count
            _mock_scalar(1),  # dup check → exists
        ])

        response = test_client.post(
            "/api/playlists",
            json={"name": "既存リスト"},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 409


class TestGetPlaylist:
    """API-006〜API-007"""

    def test_get_playlist_not_found(self, test_client, mock_session):
        """API-007: 存在しないID → 404"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result)

        response = test_client.get(
            f"/api/playlists/{uuid.uuid4()}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 404

    def test_get_playlist_forbidden(self, test_client, mock_session, sample_playlist):
        """API-009相当: 他セッション → 403"""
        sample_playlist.session_id = SESSION_ID_OTHER
        sample_playlist.playlist_tracks = []
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_playlist
        mock_session.execute = AsyncMock(return_value=result)

        response = test_client.get(
            f"/api/playlists/{sample_playlist.id}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 403


class TestUpdatePlaylist:
    """API-008〜API-009"""

    def test_update_playlist_forbidden(self, test_client, mock_session, sample_playlist):
        """API-009: 他セッションのプレイリスト更新 → 403"""
        sample_playlist.session_id = SESSION_ID_OTHER
        mock_session.get = AsyncMock(return_value=sample_playlist)

        response = test_client.patch(
            f"/api/playlists/{sample_playlist.id}",
            json={"name": "新しい名前"},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 403


class TestDeletePlaylist:
    """API-010〜API-012"""

    def test_delete_playlist_success(self, test_client, mock_session, sample_playlist):
        """API-010: 正常削除 → 204"""
        mock_session.get = AsyncMock(return_value=sample_playlist)
        mock_session.execute = AsyncMock(return_value=MagicMock())

        response = test_client.delete(
            f"/api/playlists/{sample_playlist.id}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 204

    def test_delete_playlist_forbidden(self, test_client, mock_session, sample_playlist):
        """API-011: 他セッション → 403"""
        sample_playlist.session_id = SESSION_ID_OTHER
        mock_session.get = AsyncMock(return_value=sample_playlist)

        response = test_client.delete(
            f"/api/playlists/{sample_playlist.id}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 403

    def test_delete_playlist_not_found(self, test_client, mock_session):
        """API-012: 存在しないID → 404"""
        mock_session.get = AsyncMock(return_value=None)

        response = test_client.delete(
            f"/api/playlists/{uuid.uuid4()}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 404


# ========================================
# トラック操作
# ========================================

class TestAddTracks:
    """API-020〜API-023"""

    def test_add_track_not_found(self, test_client, mock_session, sample_playlist):
        """API-022: 存在しないトラック → 404"""
        mock_session.get = AsyncMock(side_effect=[
            sample_playlist,  # _get_playlist_or_404
            None,  # track lookup
        ])
        mock_session.execute = AsyncMock(return_value=_mock_scalar(0))  # track count

        response = test_client.post(
            f"/api/playlists/{sample_playlist.id}/tracks",
            json={"track_ids": [str(uuid.uuid4())]},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 404

    def test_add_track_forbidden(self, test_client, mock_session, sample_playlist):
        """API-023: 他セッション → 403"""
        sample_playlist.session_id = SESSION_ID_OTHER
        mock_session.get = AsyncMock(return_value=sample_playlist)

        response = test_client.post(
            f"/api/playlists/{sample_playlist.id}/tracks",
            json={"track_ids": [str(uuid.uuid4())]},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 403


class TestRemoveTrack:
    """API-024〜API-025"""

    def test_remove_track_not_found(self, test_client, mock_session, sample_playlist):
        """API-025: 存在しないトラック → 404"""
        mock_session.get = AsyncMock(return_value=sample_playlist)
        result = MagicMock()
        result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=result)

        response = test_client.delete(
            f"/api/playlists/{sample_playlist.id}/tracks/{uuid.uuid4()}",
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 404


class TestReorderTracks:
    """API-026〜API-028"""

    def test_reorder_forbidden(self, test_client, mock_session, sample_playlist):
        """API-028: 他セッション → 403"""
        sample_playlist.session_id = SESSION_ID_OTHER
        mock_session.get = AsyncMock(return_value=sample_playlist)

        response = test_client.put(
            f"/api/playlists/{sample_playlist.id}/tracks/reorder",
            json={"track_ids": []},
            headers={"X-Session-ID": SESSION_ID},
        )
        assert response.status_code == 403
