"""品質スコアAPI のテスト"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.db import get_session
from api.main import app
from worker.models import Channel, TrackQualityScore


@pytest.fixture
def sample_quality_score():
    return TrackQualityScore(
        id=uuid.uuid4(),
        track_id=uuid.uuid4(),
        score=75.0,
        duration_sec=180.0,
        bit_rate=256000,
        sample_rate=48000,
        mean_volume_db=-14.0,
        max_volume_db=-1.0,
        silence_ratio=0.02,
        dynamic_range_db=13.0,
        score_details={
            "duration": 25.0,
            "mean_volume": 25.0,
            "silence": 25.0,
            "quality": 15.0,
            "dynamics": 10.0,
        },
        auto_drafted=False,
        created_at=datetime.now(timezone.utc),
    )


def _make_mock_session(execute_results):
    """execute の呼び出しごとに異なる結果を返す mock session を作成"""
    session = AsyncMock()
    if isinstance(execute_results, list):
        results = []
        for r in execute_results:
            mock_result = MagicMock()
            if isinstance(r, dict):
                for k, v in r.items():
                    setattr(mock_result, k, MagicMock(return_value=v))
            results.append(mock_result)
        session.execute.side_effect = results
    else:
        mock_result = MagicMock()
        if isinstance(execute_results, dict):
            for k, v in execute_results.items():
                setattr(mock_result, k, MagicMock(return_value=v))
        session.execute.return_value = mock_result
    return session


class TestGetTrackQuality:
    """GET /api/tracks/{track_id}/quality のテスト (AC-7)"""

    @pytest.mark.asyncio
    async def test_returns_quality_score(self, sample_quality_score):
        """スコアが存在する場合、score, details を含むレスポンスを返す"""
        qs = sample_quality_score
        session = _make_mock_session({"scalar_one_or_none": qs})

        async def override():
            yield session

        app.dependency_overrides[get_session] = override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/tracks/{qs.track_id}/quality")

            assert resp.status_code == 200
            data = resp.json()
            assert data["score"] == 75.0
            assert data["auto_drafted"] is False
            assert "score_breakdown" in data
            assert data["score_breakdown"]["duration"] == 25.0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self):
        """スコアが存在しない場合、404を返す"""
        session = _make_mock_session({"scalar_one_or_none": None})

        async def override():
            yield session

        app.dependency_overrides[get_session] = override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/tracks/{uuid.uuid4()}/quality")

            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestThresholdUpdate:
    """PATCH /api/channels/{slug}/quality/threshold のテスト (AC-8)"""

    @pytest.mark.asyncio
    async def test_update_threshold(self):
        """閾値を正常に変更できる"""
        channel = Channel(
            id=uuid.uuid4(),
            slug="lofi",
            name="Lofi",
            prompt_template="lofi",
            quality_threshold=30.0,
        )

        # 1st execute: select channel, 2nd execute: update
        session = AsyncMock()
        mock_select_result = MagicMock()
        mock_select_result.scalar_one_or_none.return_value = channel
        mock_update_result = MagicMock()
        session.execute.side_effect = [mock_select_result, mock_update_result]

        async def override():
            yield session

        app.dependency_overrides[get_session] = override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(
                    "/api/channels/lofi/quality/threshold",
                    json={"threshold": 50.0},
                )

            assert resp.status_code == 200
            data = resp.json()
            assert data["channel_slug"] == "lofi"
            assert data["threshold"] == 50.0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_threshold_rejected(self):
        """不正な閾値（> 100）→ 422 バリデーションエラー"""
        session = AsyncMock()

        async def override():
            yield session

        app.dependency_overrides[get_session] = override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(
                    "/api/channels/lofi/quality/threshold",
                    json={"threshold": 150.0},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_channel_not_found(self):
        """存在しないチャンネル → 404"""
        session = _make_mock_session({"scalar_one_or_none": None})

        async def override():
            yield session

        app.dependency_overrides[get_session] = override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(
                    "/api/channels/nonexistent/quality/threshold",
                    json={"threshold": 50.0},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()
