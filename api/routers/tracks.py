from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import NowPlayingResponse, TrackListResponse, TrackResponse
from worker.models import Channel, NowPlaying, Track

router = APIRouter(prefix="/api/channels/{slug}", tags=["tracks"])


@router.get("/tracks", response_model=TrackListResponse)
async def list_tracks(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TrackListResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    query = (
        select(Track)
        .where(Track.channel_id == channel.id)
        .order_by(Track.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = await session.execute(query)
    tracks = rows.scalars().all()

    count_result = await session.execute(
        select(func.count())
        .select_from(Track)
        .where(Track.channel_id == channel.id)
    )
    total = count_result.scalar() or 0

    items = [
        TrackResponse(
            id=t.id,
            caption=t.caption,
            duration_ms=t.duration_ms,
            bpm=t.bpm,
            music_key=t.music_key,
            instrumental=t.instrumental,
            play_count=t.play_count,
            created_at=t.created_at,
        )
        for t in tracks
    ]

    return TrackListResponse(tracks=items, total=total)


@router.get("/now-playing", response_model=NowPlayingResponse)
async def now_playing(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> NowPlayingResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    np_result = await session.execute(
        select(NowPlaying).where(NowPlaying.channel_id == channel.id)
    )
    np = np_result.scalar_one_or_none()
    if not np or not np.track_id:
        return NowPlayingResponse(track=None)

    track = await session.get(Track, np.track_id)
    if not track:
        return NowPlayingResponse(track=None)

    return NowPlayingResponse(
        track=TrackResponse(
            id=track.id,
            caption=track.caption,
            duration_ms=track.duration_ms,
            bpm=track.bpm,
            music_key=track.music_key,
            instrumental=track.instrumental,
            play_count=track.play_count,
            created_at=track.created_at,
        ),
    )
