import uuid

import pytest

from worker.models import Track
from worker.playlist_generator import generate_weighted_playlist


def _make_track(channel_id, file_path, like_count=0, is_retired=False):
    return Track(
        id=uuid.uuid4(),
        channel_id=channel_id,
        file_path=file_path,
        caption="test track",
        like_count=like_count,
        is_retired=is_retired,
    )


class FakeScalarsResult:
    """session.execute().scalars().all() をシミュレート。"""

    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalarsResult(self._items)


class TestGenerateWeightedPlaylist:
    @pytest.mark.asyncio
    async def test_generates_playlist_file(self, tmp_path):
        """プレイリストが正しく生成される。"""
        channel_id = uuid.uuid4()
        channel_slug = "lofi"
        tracks_dir = str(tmp_path / "tracks")

        # テスト用FLACファイルを作成
        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        for i in range(3):
            (ch_dir / f"track{i}.flac").write_bytes(b"fake")

        tracks = [
            _make_track(channel_id, f"{channel_slug}/track{i}.flac", like_count=i)
            for i in range(3)
        ]

        from unittest.mock import AsyncMock

        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult(tracks))

        count = await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        assert playlist_path.exists()
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) > 0
        assert count == 3

    @pytest.mark.asyncio
    async def test_weight_increases_with_likes(self, tmp_path):
        """like_count が多いトラックほどプレイリスト内の出現回数が増える。"""
        channel_id = uuid.uuid4()
        channel_slug = "ambient"
        tracks_dir = str(tmp_path / "tracks")

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        (ch_dir / "popular.flac").write_bytes(b"fake")
        (ch_dir / "normal.flac").write_bytes(b"fake")

        popular = _make_track(channel_id, f"{channel_slug}/popular.flac", like_count=10)
        normal = _make_track(channel_id, f"{channel_slug}/normal.flac", like_count=1)

        from unittest.mock import AsyncMock

        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult([popular, normal]))

        await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = content.strip().split("\n")

        popular_count = sum(1 for line in lines if "popular.flac" in line)
        normal_count = sum(1 for line in lines if "normal.flac" in line)
        assert popular_count == 10
        assert normal_count == 1

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_tracks(self, tmp_path):
        """トラックがない場合は 0 を返す。"""
        channel_id = uuid.uuid4()
        tracks_dir = str(tmp_path / "tracks")

        from unittest.mock import AsyncMock

        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult([]))

        count = await generate_weighted_playlist(
            session, channel_id, "lofi", tracks_dir,
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_skips_missing_files(self, tmp_path):
        """ファイルが存在しないトラックはプレイリストに含まれない。"""
        channel_id = uuid.uuid4()
        channel_slug = "lofi"
        tracks_dir = str(tmp_path / "tracks")

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        # track0 のみファイルを作成、track1 はファイルなし
        (ch_dir / "track0.flac").write_bytes(b"fake")

        tracks = [
            _make_track(channel_id, f"{channel_slug}/track0.flac", like_count=1),
            _make_track(channel_id, f"{channel_slug}/track1.flac", like_count=1),
        ]

        from unittest.mock import AsyncMock

        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult(tracks))

        count = await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert count == 1
        assert all("track0.flac" in line for line in lines)
