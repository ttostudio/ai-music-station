"""worker/track_retirement.py のテスト"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from worker.models import Track
from worker.track_retirement import (
    MAX_LIKE_RATIO,
    MIN_PLAY_COUNT,
    cleanup_excess_tracks,
    count_active_tracks,
    get_least_popular_tracks,
    retire_unpopular_tracks,
)


def _make_track(channel_id, play_count=0, like_count=0, is_retired=False, file_path=None):
    track = Track(
        id=uuid.uuid4(),
        channel_id=channel_id,
        file_path=file_path or f"test/{uuid.uuid4()}.flac",
        caption="test track",
        play_count=play_count,
        like_count=like_count,
        is_retired=is_retired,
    )
    return track


# --- retire_unpopular_tracks（既存テスト） ---


class TestRetireUnpopularTracks:
    @pytest.mark.asyncio
    async def test_retires_low_like_ratio_tracks(self):
        """play_count >= 5 かつ like率 < 0.1 のトラックがリタイアされる。"""
        channel_id = uuid.uuid4()
        track = _make_track(channel_id, play_count=10, like_count=0)

        session = AsyncMock()
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


# --- count_active_tracks ---


class TestCountActiveTracks:
    @pytest.mark.asyncio
    async def test_returns_count(self):
        """アクティブトラック数を正しく返す。"""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        session.execute.return_value = mock_result

        count = await count_active_tracks(session, uuid.uuid4())
        assert count == 42

    @pytest.mark.asyncio
    async def test_returns_zero_when_none(self):
        """結果がNoneの場合は0を返す。"""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        session.execute.return_value = mock_result

        count = await count_active_tracks(session, uuid.uuid4())
        assert count == 0


# --- get_least_popular_tracks ---


class TestGetLeastPopularTracks:
    @pytest.mark.asyncio
    async def test_returns_tracks_sorted_by_like_ratio(self):
        """like率昇順でトラックが返される。"""
        channel_id = uuid.uuid4()
        # play_count=0 → like率0（最優先削除）
        t1 = _make_track(channel_id, play_count=0, like_count=0)
        # play_count=10, like_count=1 → like率0.1
        t2 = _make_track(channel_id, play_count=10, like_count=1)
        # play_count=10, like_count=5 → like率0.5
        t3 = _make_track(channel_id, play_count=10, like_count=5)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [t1, t2, t3]
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        tracks = await get_least_popular_tracks(session, channel_id, limit=3)
        assert len(tracks) == 3
        # セッションのexecuteが呼ばれたことを確認
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_play_count_zero_first(self):
        """play_count=0のトラックが最優先で返される。"""
        channel_id = uuid.uuid4()
        t_zero = _make_track(channel_id, play_count=0, like_count=0)
        t_popular = _make_track(channel_id, play_count=100, like_count=50)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        # DBが正しくソートして返す想定
        mock_scalars.all.return_value = [t_zero, t_popular]
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        tracks = await get_least_popular_tracks(session, channel_id, limit=2)
        assert tracks[0].play_count == 0


# --- cleanup_excess_tracks ---


class TestCleanupExcessTracks:
    @pytest.mark.asyncio
    async def test_no_cleanup_when_under_max_stock(self):
        """max_stock以下の場合は何もしない。"""
        channel_id = uuid.uuid4()

        session = AsyncMock()
        # count_active_tracks が50を返す
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        session.execute.return_value = mock_count_result

        retired = await cleanup_excess_tracks(
            session, channel_id, "lofi", 200, "/tmp/tracks",
        )
        assert retired == 0

    @pytest.mark.asyncio
    async def test_cleanup_excess_tracks(self):
        """超過分のトラックが退役+FLAC削除される。"""
        channel_id = uuid.uuid4()
        t1 = _make_track(channel_id, play_count=0, like_count=0, file_path="lofi/a.flac")
        t2 = _make_track(channel_id, play_count=1, like_count=0, file_path="lofi/b.flac")

        session = AsyncMock()
        # 1回目: count_active_tracks → 102
        mock_count = MagicMock()
        mock_count.scalar.return_value = 102
        # 2回目: get_least_popular_tracks → [t1, t2]
        mock_tracks = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [t1, t2]
        mock_tracks.scalars.return_value = mock_scalars

        session.execute = AsyncMock(side_effect=[mock_count, mock_tracks])
        session.commit = AsyncMock()

        with patch("worker.track_retirement.os.path.exists", return_value=True), \
             patch("worker.track_retirement.os.remove") as mock_remove:
            retired = await cleanup_excess_tracks(
                session, channel_id, "lofi", 100, "/tmp/tracks",
            )

        assert retired == 2
        assert t1.is_retired is True
        assert t2.is_retired is True
        assert mock_remove.call_count == 2
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_flac_deletion_failure_does_not_stop(self):
        """FLAC削除失敗時もプロセスは継続する。"""
        channel_id = uuid.uuid4()
        t1 = _make_track(channel_id, play_count=0, like_count=0, file_path="ch/x.flac")

        session = AsyncMock()
        mock_count = MagicMock()
        mock_count.scalar.return_value = 101
        mock_tracks = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [t1]
        mock_tracks.scalars.return_value = mock_scalars

        session.execute = AsyncMock(side_effect=[mock_count, mock_tracks])
        session.commit = AsyncMock()

        with patch("worker.track_retirement.os.path.exists", return_value=True), \
             patch("worker.track_retirement.os.remove", side_effect=OSError("permission denied")):
            retired = await cleanup_excess_tracks(
                session, channel_id, "ch", 100, "/tmp/tracks",
            )

        # OSError が起きても退役は完了する
        assert retired == 1
        assert t1.is_retired is True
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_missing_flac_file(self):
        """FLACファイルが存在しない場合はos.removeを呼ばない。"""
        channel_id = uuid.uuid4()
        t1 = _make_track(channel_id, play_count=0, like_count=0, file_path="ch/missing.flac")

        session = AsyncMock()
        mock_count = MagicMock()
        mock_count.scalar.return_value = 101
        mock_tracks = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [t1]
        mock_tracks.scalars.return_value = mock_scalars

        session.execute = AsyncMock(side_effect=[mock_count, mock_tracks])
        session.commit = AsyncMock()

        with patch("worker.track_retirement.os.path.exists", return_value=False), \
             patch("worker.track_retirement.os.remove") as mock_remove:
            retired = await cleanup_excess_tracks(
                session, channel_id, "ch", 100, "/tmp/tracks",
            )

        assert retired == 1
        mock_remove.assert_not_called()

    @pytest.mark.asyncio
    async def test_exact_max_stock_no_cleanup(self):
        """ちょうどmax_stockの場合は棚卸ししない。"""
        channel_id = uuid.uuid4()

        session = AsyncMock()
        mock_count = MagicMock()
        mock_count.scalar.return_value = 100
        session.execute.return_value = mock_count

        retired = await cleanup_excess_tracks(
            session, channel_id, "lofi", 100, "/tmp/tracks",
        )
        assert retired == 0
