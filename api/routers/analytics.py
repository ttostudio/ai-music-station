"""アナリティクス API — 再生トラッキング / 統計"""
from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_session
from api.schemas import PlayEventBody, PlayEventResponse, TrackStatsResponse
from worker.models import ShareLink, Track, TrackAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(
        (ip + settings.analytics_ip_salt).encode()
    ).hexdigest()


@router.post("/play", response_model=PlayEventResponse, status_code=202)
async def record_play(
    body: PlayEventBody,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> PlayEventResponse:
    """再生イベントを記録する（fire-and-forget）"""
    # トラック存在確認
    track = await session.get(Track, str(body.track_id))
    if not track or track.is_retired:
        raise HTTPException(status_code=404, detail="Track not found")

    # share_token 検証（存在しなくてもエラーにしない、null として記録）
    resolved_token: str | None = None
    if body.share_token:
        result = await session.execute(
            select(ShareLink).where(ShareLink.share_token == body.share_token)
        )
        if result.scalar_one_or_none():
            resolved_token = body.share_token

    # イベント記録（失敗しても 202 を返す）
    try:
        ip = request.client.host if request.client else ""
        analytics = TrackAnalytics(
            track_id=track.id,
            event_type="play",
            ip_hash=_hash_ip(ip) if ip else None,
            user_agent=(request.headers.get("user-agent") or "")[:500] or None,
            referer=(request.headers.get("referer") or "")[:500] or None,
            share_token=resolved_token,
        )
        session.add(analytics)
        await session.commit()
    except Exception:
        logger.warning("Failed to record play event", exc_info=True)

    return PlayEventResponse(ok=True)


@router.get("/tracks/{track_id}/stats", response_model=TrackStatsResponse)
async def get_track_stats(
    track_id: str,
    session: AsyncSession = Depends(get_session),
) -> TrackStatsResponse:
    """トラックの再生・共有統計を取得する"""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # share_links カウント
    share_result = await session.execute(
        select(func.count()).select_from(ShareLink).where(
            ShareLink.track_id == track.id
        )
    )
    share_count = share_result.scalar() or 0

    # ソース別再生数（share_token の有無で分類）
    play_total_result = await session.execute(
        select(func.count()).select_from(TrackAnalytics).where(
            TrackAnalytics.track_id == track.id,
            TrackAnalytics.event_type == "play",
        )
    )
    play_total = play_total_result.scalar() or 0

    share_play_result = await session.execute(
        select(func.count()).select_from(TrackAnalytics).where(
            TrackAnalytics.track_id == track.id,
            TrackAnalytics.event_type == "play",
            TrackAnalytics.share_token.is_not(None),
        )
    )
    share_plays = share_play_result.scalar() or 0
    direct_plays = play_total - share_plays

    return TrackStatsResponse(
        track_id=track.id,
        play_count=track.play_count,
        share_count=share_count,
        like_count=track.like_count,
        plays_by_source={"direct": direct_plays, "share_page": share_plays},
    )
