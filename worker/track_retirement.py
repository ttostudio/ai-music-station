"""不人気トラックの棚卸し（リタイア判定）モジュール。"""

from __future__ import annotations

import logging

from sqlalchemy import select, update
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
