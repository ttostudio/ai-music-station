"""Podcast エピソード API（読み取り専用）

エピソード生成はホスト側の podcast_generator で実行される。
APIはDB内のエピソードデータを公開するのみ。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import (
    PodcastEpisodeListResponse,
    PodcastEpisodeResponse,
)
from worker.models import PodcastEpisode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/podcast", tags=["podcast"])


@router.get("/episodes", response_model=PodcastEpisodeListResponse)
async def list_episodes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PodcastEpisodeListResponse:
    """ポッドキャストエピソード一覧"""
    total_q = await session.execute(select(func.count(PodcastEpisode.id)))
    total = total_q.scalar() or 0

    result = await session.execute(
        select(PodcastEpisode)
        .order_by(PodcastEpisode.episode_number.desc())
        .limit(limit)
        .offset(offset)
    )
    episodes = result.scalars().all()

    return PodcastEpisodeListResponse(
        episodes=[
            PodcastEpisodeResponse(
                id=ep.id,
                article_slug=ep.article_slug,
                title=ep.title,
                description=ep.description,
                duration_ms=ep.duration_ms,
                episode_number=ep.episode_number,
                status=ep.status,
                created_at=ep.created_at,
            )
            for ep in episodes
        ],
        total=total,
    )
