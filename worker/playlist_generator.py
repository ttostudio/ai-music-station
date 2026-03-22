"""重み付きシャッフルプレイリスト生成モジュール。"""

from __future__ import annotations

import logging
import random
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models import PodcastEpisode, Track

logger = logging.getLogger(__name__)


async def generate_weighted_playlist(
    session: AsyncSession,
    channel_id,
    channel_slug: str,
    tracks_dir: str,
    playlist_tracks_dir: str | None = None,  # Liquidsoap 用パス（省略時は tracks_dir）
) -> int:
    """like_count による重み付きシャッフルプレイリストを生成する。

    - is_retired=false のトラックのみ対象
    - weight = max(1, like_count)
    - 各トラックを weight 回リストに追加してシャッフル
    - generated_tracks/{channel_slug}/playlist.m3u に書き出し

    playlist_tracks_dir: M3U エントリに書き込むベースパス。
      Liquidsoap コンテナ内パス（例: /tracks）を指定することで、
      ファイル存在チェック（ホスト側）と M3U エントリ（コンテナ側）を分離できる。
      省略時は tracks_dir と同じパスを使用（後方互換）。

    戻り値: プレイリストに含まれるユニークトラック数。
    """
    result = await session.execute(
        select(Track).where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
        )
    )
    tracks = result.scalars().all()

    if not tracks:
        return 0

    # 重み付きリスト作成
    weighted_entries: list[str] = []
    base_dir = Path(tracks_dir)
    # M3U エントリ用ベースパス（指定なければ tracks_dir と同じ — テスト互換）
    playlist_base = Path(playlist_tracks_dir) if playlist_tracks_dir else base_dir
    for track in tracks:
        host_path = base_dir / track.file_path        # ファイル存在チェック用（ホスト側）
        container_path = playlist_base / track.file_path  # M3U エントリ用（コンテナ側）
        if not host_path.exists():
            continue
        weight = max(1, track.like_count)
        weighted_entries.extend([str(container_path)] * weight)

    random.shuffle(weighted_entries)

    # プレイリスト書き出し
    playlist_dir = base_dir / channel_slug
    playlist_dir.mkdir(parents=True, exist_ok=True)
    playlist_path = playlist_dir / "playlist.m3u"
    playlist_path.write_text("\n".join(weighted_entries) + "\n", encoding="utf-8")

    unique_count = len({e for e in weighted_entries})
    logger.info(
        "チャンネル %s: プレイリスト生成 (%d トラック, %d エントリ)",
        channel_slug, unique_count, len(weighted_entries),
    )
    return unique_count


async def generate_podcast_playlist(
    session: AsyncSession,
    channel_id,
    channel_slug: str,
    tracks_dir: str,
) -> int:
    """ポッドキャストエピソードの順序再生プレイリストを生成する。

    エピソード番号順に並べる（シャッフルなし）。
    戻り値: プレイリストに含まれるエピソード数。
    """
    result = await session.execute(
        select(PodcastEpisode)
        .where(
            PodcastEpisode.channel_id == channel_id,
            PodcastEpisode.status == "published",
        )
        .order_by(PodcastEpisode.episode_number.asc())
    )
    episodes = result.scalars().all()

    if not episodes:
        return 0

    entries: list[str] = []
    for ep in episodes:
        audio_path = Path(ep.audio_file_path)
        if audio_path.exists():
            entries.append(str(audio_path))

    base_dir = Path(tracks_dir)
    playlist_dir = base_dir / channel_slug
    playlist_dir.mkdir(parents=True, exist_ok=True)
    playlist_path = playlist_dir / "playlist.m3u"
    playlist_path.write_text("\n".join(entries) + "\n", encoding="utf-8")

    logger.info(
        "ポッドキャスト %s: プレイリスト生成 (%d エピソード)",
        channel_slug, len(entries),
    )
    return len(entries)
