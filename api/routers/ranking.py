"""人気楽曲ランキング API — チャンネル別 like_count 上位トラック"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import ChannelRankingResponse, RankingTrackResponse
from worker.models import Channel, Track

router = APIRouter(tags=["ranking"])


@router.get("/api/channels/{slug}/ranking", response_model=ChannelRankingResponse)
async def get_channel_ranking(
    slug: str,
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
) -> ChannelRankingResponse:
    """チャンネル別人気楽曲ランキングを取得する（like_count 降順）"""
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    tracks_result = await session.execute(
        select(Track)
        .where(
            Track.channel_id == channel.id,
            Track.is_retired == False,  # noqa: E712
        )
        .order_by(Track.like_count.desc(), Track.play_count.desc())
        .limit(limit)
    )
    tracks = tracks_result.scalars().all()

    ranking = [
        RankingTrackResponse(
            rank=i + 1,
            id=t.id,
            title=t.title,
            caption=t.caption,
            like_count=t.like_count,
            play_count=t.play_count,
            duration_ms=t.duration_ms,
            bpm=t.bpm,
        )
        for i, t in enumerate(tracks)
    ]

    return ChannelRankingResponse(channel_slug=slug, tracks=ranking)
