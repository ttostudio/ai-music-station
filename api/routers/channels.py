from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import (
    ChannelDetailResponse,
    ChannelListResponse,
    ChannelResponse,
    NowPlayingInfo,
)
from worker.models import Channel, NowPlaying, Request, Track

router = APIRouter(prefix="/api/channels", tags=["channels"])


async def _channel_to_response(
    session: AsyncSession, channel: Channel,
) -> ChannelResponse:
    pending_count = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(Request.channel_id == channel.id, Request.status == "pending")
    )
    queue_depth = pending_count.scalar() or 0

    track_count = await session.execute(
        select(func.count())
        .select_from(Track)
        .where(Track.channel_id == channel.id)
    )
    total_tracks = track_count.scalar() or 0

    now_playing_row = await session.execute(
        select(NowPlaying).where(NowPlaying.channel_id == channel.id)
    )
    np = now_playing_row.scalar_one_or_none()
    now_playing = None
    if np and np.track_id:
        track = await session.get(Track, np.track_id)
        if track:
            now_playing = NowPlayingInfo(
                track_id=track.id,
                caption=track.caption,
                started_at=np.started_at,
            )

    return ChannelResponse(
        id=channel.id,
        slug=channel.slug,
        name=channel.name,
        description=channel.description,
        is_active=channel.is_active,
        queue_depth=queue_depth,
        total_tracks=total_tracks,
        stream_url=f"/stream/{channel.slug}.ogg",
        now_playing=now_playing,
    )


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    session: AsyncSession = Depends(get_session),
) -> ChannelListResponse:
    result = await session.execute(
        select(Channel).where(Channel.is_active.is_(True)).order_by(Channel.slug)
    )
    channels = result.scalars().all()
    responses = [await _channel_to_response(session, c) for c in channels]
    return ChannelListResponse(channels=responses)


@router.get("/{slug}", response_model=ChannelDetailResponse)
async def get_channel(
    slug: str, session: AsyncSession = Depends(get_session),
) -> ChannelDetailResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    base = await _channel_to_response(session, channel)
    return ChannelDetailResponse(
        **base.model_dump(),
        default_bpm_min=channel.default_bpm_min,
        default_bpm_max=channel.default_bpm_max,
        default_duration=channel.default_duration,
        default_instrumental=channel.default_instrumental,
    )
