"""重み付きシャッフルプレイリスト生成モジュール。"""

from __future__ import annotations

import logging
import random
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models import Track

logger = logging.getLogger(__name__)


async def generate_weighted_playlist(
    session: AsyncSession,
    channel_id,
    channel_slug: str,
    tracks_dir: str,
) -> int:
    """like_count による重み付きシャッフルプレイリストを生成する。

    - is_retired=false のトラックのみ対象
    - weight = max(1, like_count)
    - 各トラックを weight 回リストに追加してシャッフル
    - generated_tracks/{channel_slug}/playlist.m3u に書き出し

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
    for track in tracks:
        full_path = base_dir / track.file_path
        if not full_path.exists():
            continue
        weight = max(1, track.like_count)
        weighted_entries.extend([str(full_path)] * weight)

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
