import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from worker.models import Track
from worker.track_retirement import (
    MAX_LIKE_RATIO,
    MIN_PLAY_COUNT,
    retire_unpopular_tracks,
)


def _make_track(channel_id, play_count=0, like_count=0, is_retired=False):
    track = Track(
        id=uuid.uuid4(),
        channel_id=channel_id,
        file_path=f"test/{uuid.uuid4()}.flac",
        caption="test track",
        play_count=play_count,
        like_count=like_count,
        is_retired=is_retired,
    )
    return track


class TestRetireUnpopularTracks:
    @pytest.mark.asyncio
    async def test_retires_low_like_ratio_tracks(self):
        """play_count >= 5 かつ like率 < 0.1 のトラックがリタイアされる。"""
        channel_id = uuid.uuid4()
        # play_count=10, like_count=0 → like率 0.0 → リタイア対象
        track = _make_track(channel_id, play_count=10, like_count=0)

        session = AsyncMock()
        # select で候補IDを返す
        select_result = MagicMock()
        select_result.all.return_value = [(track.id,)]
        session.execute = AsyncMock(side_effect=[select_result, MagicMock()])
        session.get = AsyncMock(return_value=track)
        session.commit = AsyncMock()

        retired = await retire_unpopular_tracks(session, channel_id)
        assert retired == 1

    @pytest.mark.asyncio
    async def test_skips_tracks_with_good_like_ratio(self):
        """like率が十分なトラックはリタイアしない。"""
        channel_id = uuid.uuid4()
        # play_count=10, like_count=5 → like率 0.5 → リタイアしない
        track = _make_track(channel_id, play_count=10, like_count=5)

        session = AsyncMock()
        select_result = MagicMock()
        select_result.all.return_value = [(track.id,)]
        session.execute = AsyncMock(return_value=select_result)
        session.get = AsyncMock(return_value=track)

        retired = await retire_unpopular_tracks(session, channel_id)
        assert retired == 0

    @pytest.mark.asyncio
    async def test_skips_tracks_below_min_play_count(self):
        """play_count が閾値未満のトラックは候補にならない。"""
        channel_id = uuid.uuid4()

        session = AsyncMock()
        # SQLクエリが候補を返さない
        select_result = MagicMock()
        select_result.all.return_value = []
        session.execute = AsyncMock(return_value=select_result)

        retired = await retire_unpopular_tracks(session, channel_id)
        assert retired == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_candidates(self):
        """候補がない場合は 0 を返す。"""
        channel_id = uuid.uuid4()
        session = AsyncMock()
        select_result = MagicMock()
        select_result.all.return_value = []
        session.execute = AsyncMock(return_value=select_result)

        retired = await retire_unpopular_tracks(session, channel_id)
        assert retired == 0

    def test_threshold_constants(self):
        """閾値定数が想定通りの値。"""
        assert MIN_PLAY_COUNT == 5
        assert MAX_LIKE_RATIO == 0.1
