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


class TestPlaylistGeneratorPathFix:
    """FR-110: Liquidsoap コンテナパス修正のテスト (R-01〜R-05)"""

    def _make_session(self, tracks):
        from unittest.mock import AsyncMock
        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult(tracks))
        return session

    @pytest.mark.asyncio
    async def test_r01_absolute_path_in_playlist(self, tmp_path):
        """R-01: playlist_tracks_dir 指定時、M3Uエントリが絶対パスであること。"""
        channel_id = uuid.uuid4()
        channel_slug = "egusugi"
        tracks_dir = str(tmp_path / "tracks")
        playlist_tracks_dir = "/tracks"

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        (ch_dir / "song.flac").write_bytes(b"fake")

        tracks = [_make_track(channel_id, f"{channel_slug}/song.flac", like_count=1)]
        session = self._make_session(tracks)

        await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 1
        assert lines[0].startswith("/"), f"絶対パスではない: {lines[0]}"

    @pytest.mark.asyncio
    async def test_r02_no_relative_path_in_playlist(self, tmp_path):
        """R-02: playlist_tracks_dir 指定時、M3Uエントリが相対パス（./や../）でないこと。"""
        channel_id = uuid.uuid4()
        channel_slug = "egusugi"
        tracks_dir = str(tmp_path / "tracks")
        playlist_tracks_dir = "/tracks"

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        (ch_dir / "song.flac").write_bytes(b"fake")

        tracks = [_make_track(channel_id, f"{channel_slug}/song.flac", like_count=1)]
        session = self._make_session(tracks)

        await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        for line in lines:
            assert not line.startswith("./"), f"相対パス（./）が含まれている: {line}"
            assert not line.startswith("../"), f"相対パス（../）が含まれている: {line}"

    @pytest.mark.asyncio
    async def test_r03_missing_file_excluded_from_playlist(self, tmp_path):
        """R-03: ファイルが存在しないトラックはM3Uに含まれないこと。"""
        channel_id = uuid.uuid4()
        channel_slug = "egusugi"
        tracks_dir = str(tmp_path / "tracks")
        playlist_tracks_dir = "/tracks"

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        (ch_dir / "existing_song.flac").write_bytes(b"fake")

        tracks = [
            _make_track(channel_id, f"{channel_slug}/existing_song.flac", like_count=1),
            _make_track(channel_id, f"{channel_slug}/missing_song.flac", like_count=1),
        ]
        session = self._make_session(tracks)

        count = await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert count == 1
        assert all("existing_song.flac" in line for line in lines)
        assert all("missing_song.flac" not in line for line in lines)

    @pytest.mark.asyncio
    async def test_r04_container_path_used_in_m3u_entry(self, tmp_path):
        """R-04: M3Uエントリが playlist_tracks_dir（コンテナ側パス）を使用すること。"""
        channel_id = uuid.uuid4()
        channel_slug = "egusugi"
        tracks_dir = str(tmp_path / "tracks")
        playlist_tracks_dir = "/tracks"

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        (ch_dir / "song.flac").write_bytes(b"fake")

        tracks = [_make_track(channel_id, f"{channel_slug}/song.flac", like_count=1)]
        session = self._make_session(tracks)

        await generate_weighted_playlist(
            session, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )

        playlist_path = ch_dir / "playlist.m3u"
        content = playlist_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert lines[0] == f"/tracks/{channel_slug}/song.flac", (
            f"期待: /tracks/{channel_slug}/song.flac, 実際: {lines[0]}"
        )
        assert str(tmp_path) not in lines[0]

    @pytest.mark.asyncio
    async def test_r05_path_generation_reproducibility(self, tmp_path):
        """R-05: 同じ入力に対して生成されるM3Uエントリパスが毎回同一であること。"""
        channel_id = uuid.uuid4()
        channel_slug = "egusugi"
        tracks_dir = str(tmp_path / "tracks")
        playlist_tracks_dir = "/tracks"

        ch_dir = tmp_path / "tracks" / channel_slug
        ch_dir.mkdir(parents=True)
        for i in range(3):
            (ch_dir / f"song{i}.flac").write_bytes(b"fake")

        tracks = [
            _make_track(channel_id, f"{channel_slug}/song{i}.flac", like_count=1)
            for i in range(3)
        ]

        from unittest.mock import AsyncMock

        session1 = AsyncMock()
        session1.execute = AsyncMock(return_value=FakeExecuteResult(tracks))
        await generate_weighted_playlist(
            session1, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )
        content1 = (ch_dir / "playlist.m3u").read_text()
        paths1 = set(content1.strip().split("\n"))

        session2 = AsyncMock()
        session2.execute = AsyncMock(return_value=FakeExecuteResult(tracks))
        await generate_weighted_playlist(
            session2, channel_id, channel_slug, tracks_dir,
            playlist_tracks_dir=playlist_tracks_dir,
        )
        content2 = (ch_dir / "playlist.m3u").read_text()
        paths2 = set(content2.strip().split("\n"))

        assert paths1 == paths2
        for path in paths1:
            if path:
                assert path.startswith("/tracks/"), f"コンテナパスではない: {path}"
