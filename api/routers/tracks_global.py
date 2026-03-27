from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import TrackSearchListResponse, TrackSearchResponse
from worker.models import Channel, Track

router = APIRouter(prefix="/api/tracks", tags=["tracks"])

TRACKS_ROOT = Path("/tracks")


@router.get("/{track_id}/audio")
async def get_track_audio(
    track_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="トラックが見つかりません")

    raw_path = Path(track.file_path)
    try:
        rel = raw_path.relative_to("/tracks")
        abs_path = TRACKS_ROOT / rel
    except ValueError:
        abs_path = TRACKS_ROOT / raw_path

    abs_path = abs_path.resolve()
    if not abs_path.is_relative_to(TRACKS_ROOT.resolve()):
        raise HTTPException(status_code=404, detail="音声ファイルが見つかりません")

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="音声ファイルが見つかりません")

    return FileResponse(
        path=str(abs_path),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=3600, immutable",
            "Accept-Ranges": "bytes",
        },
    )


@router.get("/search", response_model=TrackSearchListResponse)
async def search_tracks(
    q: str | None = Query(None, max_length=200),
    mood: str | None = Query(None, max_length=100),
    channel_slug: str | None = Query(None, max_length=50, pattern=r'^[a-z0-9-]+$'),
    sort: Literal["popular", "newest", "score"] = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TrackSearchListResponse:
    query = (
        select(Track, Channel)
        .join(Channel, Track.channel_id == Channel.id)
        .where(Track.is_retired == False)  # noqa: E712
    )

    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Track.title.ilike(search_term),
                Track.mood.ilike(search_term),
                Track.caption.ilike(search_term),
            )
        )

    if mood:
        query = query.where(Track.mood == mood)

    if channel_slug:
        query = query.where(Channel.slug == channel_slug)

    sort_map = {
        "newest": [Track.created_at.desc()],
        "popular": [Track.play_count.desc(), Track.created_at.desc()],
        "score": [Track.quality_score.desc().nulls_last(), Track.created_at.desc()],
    }
    query = query.order_by(*sort_map[sort])

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    rows = await session.execute(query.offset(offset).limit(limit))
    results = rows.all()

    items = [
        TrackSearchResponse(
            id=t.id,
            title=t.title,
            caption=t.caption,
            mood=t.mood,
            duration_ms=t.duration_ms,
            bpm=t.bpm,
            music_key=t.music_key,
            instrumental=t.instrumental,
            play_count=t.play_count,
            like_count=t.like_count,
            quality_score=t.quality_score,
            channel_slug=c.slug,
            created_at=t.created_at,
        )
        for t, c in results
    ]

    return TrackSearchListResponse(tracks=items, total=total, limit=limit, offset=offset)
