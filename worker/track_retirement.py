"""不人気トラックの棚卸し（リタイア判定）モジュール。"""

from __future__ import annotations

import logging
import os

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models import Track

logger = logging.getLogger(__name__)

# 棚卸し判定の閾値
MIN_PLAY_COUNT = 5
MAX_LIKE_RATIO = 0.1


async def retire_unpopular_tracks(session: AsyncSession, channel_id) -> int:
    """play_count >= MIN_PLAY_COUNT かつ like率 < MAX_LIKE_RATIO のトラックをリタイアさせる。

    FLACファイルは保持（将来復活用）。
    戻り値: リタイアさせたトラック数。
    """
    # リタイア対象のトラックIDを取得
    result = await session.execute(
        select(Track.id).where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
            Track.play_count >= MIN_PLAY_COUNT,
        )
    )
    candidate_ids = []
    for (track_id,) in result.all():
        track = await session.get(Track, track_id)
        if track and track.play_count > 0:
            like_ratio = track.like_count / track.play_count
            if like_ratio < MAX_LIKE_RATIO:
                candidate_ids.append(track_id)

    if not candidate_ids:
        return 0

    await session.execute(
        update(Track)
        .where(Track.id.in_(candidate_ids))
        .values(is_retired=True)
    )
    await session.commit()

    logger.info(
        "チャンネル %s: %d トラックをリタイア",
        channel_id, len(candidate_ids),
    )
    return len(candidate_ids)


async def count_active_tracks(session: AsyncSession, channel_id) -> int:
    """チャンネルのアクティブ（未リタイア）トラック数を返す。"""
    result = await session.execute(
        select(func.count(Track.id)).where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
        )
    )
    return result.scalar() or 0


async def get_least_popular_tracks(
    session: AsyncSession, channel_id, *, limit: int,
) -> list[Track]:
    """不人気順（like率昇順）にトラックを取得する。

    like率 = like_count / max(play_count, 1)
    play_count=0 の曲は like率=0 となり最優先で削除される。
    """
    like_ratio = case(
        (Track.play_count == 0, 0.0),
        else_=Track.like_count * 1.0 / Track.play_count,
    )
    result = await session.execute(
        select(Track)
        .where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
        )
        .order_by(like_ratio.asc(), Track.play_count.asc(), Track.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def cleanup_excess_tracks(
    session: AsyncSession,
    channel_id,
    channel_slug: str,
    max_stock: int,
    tracks_dir: str,
) -> int:
    """max_stockを超過した不人気トラックを退役+FLAC削除する。

    戻り値: 退役させたトラック数。
    """
    count = await count_active_tracks(session, channel_id)
    if count <= max_stock:
        return 0

    excess = count - max_stock
    tracks_to_retire = await get_least_popular_tracks(
        session, channel_id, limit=excess,
    )

    retired = 0
    for track in tracks_to_retire:
        track.is_retired = True

        # FLACファイルを物理削除（ディスク節約）
        file_path = os.path.join(tracks_dir, track.file_path)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("FLAC削除: %s", file_path)
        except OSError as e:
            logger.warning("FLAC削除失敗: %s: %s", file_path, e)

        retired += 1

    if retired > 0:
        await session.commit()
        logger.info(
            "チャンネル %s: %d曲を棚卸し（%d→%d）",
            channel_slug, retired, count, count - retired,
        )
    return retired
