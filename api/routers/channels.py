from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import (
    ChannelCreateBody,
    ChannelDetailResponse,
    ChannelFullResponse,
    ChannelListResponse,
    ChannelResponse,
    ChannelUpdateBody,
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
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    base = await _channel_to_response(session, channel)
    return ChannelDetailResponse(
        **base.model_dump(),
        default_bpm_min=channel.default_bpm_min,
        default_bpm_max=channel.default_bpm_max,
        default_duration=channel.default_duration,
        default_instrumental=channel.default_instrumental,
    )


@router.patch("/{slug}", response_model=ChannelDetailResponse)
async def patch_channel(
    slug: str,
    body: ChannelUpdateBody,
    session: AsyncSession = Depends(get_session),
) -> ChannelDetailResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=404, detail="チャンネルが見つかりません",
        )

    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(channel, key, value)
    await session.commit()
    await session.refresh(channel)

    base = await _channel_to_response(session, channel)
    return ChannelDetailResponse(
        **base.model_dump(),
        default_bpm_min=channel.default_bpm_min,
        default_bpm_max=channel.default_bpm_max,
        default_duration=channel.default_duration,
        default_instrumental=channel.default_instrumental,
    )


def _channel_to_full_response(channel: Channel) -> ChannelFullResponse:
    return ChannelFullResponse(
        id=channel.id,
        slug=channel.slug,
        name=channel.name,
        description=channel.description,
        mood_description=channel.mood_description,
        is_active=channel.is_active,
        default_bpm_min=channel.default_bpm_min,
        default_bpm_max=channel.default_bpm_max,
        default_duration=channel.default_duration,
        default_key=channel.default_key,
        default_instrumental=channel.default_instrumental,
        prompt_template=channel.prompt_template,
        vocal_language=channel.vocal_language,
        auto_generate=channel.auto_generate,
        min_stock=channel.min_stock,
        max_stock=channel.max_stock,
    )


@router.post("", response_model=ChannelFullResponse, status_code=201)
async def create_channel(
    body: ChannelCreateBody,
    session: AsyncSession = Depends(get_session),
) -> ChannelFullResponse:
    existing = await session.execute(
        select(Channel).where(Channel.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="このスラッグは既に使用されています",
        )

    channel = Channel(**body.model_dump())
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return _channel_to_full_response(channel)


@router.put("/{slug}", response_model=ChannelFullResponse)
async def update_channel(
    slug: str,
    body: ChannelCreateBody,
    session: AsyncSession = Depends(get_session),
) -> ChannelFullResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=404, detail="チャンネルが見つかりません",
        )

    data = body.model_dump(exclude={"slug"})
    for key, value in data.items():
        setattr(channel, key, value)
    await session.commit()
    await session.refresh(channel)
    return _channel_to_full_response(channel)


@router.delete("/{slug}")
async def delete_channel(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=404, detail="チャンネルが見つかりません",
        )

    # Count tracks to retire
    track_count_result = await session.execute(
        select(func.count())
        .select_from(Track)
        .where(Track.channel_id == channel.id, Track.is_retired.is_(False))
    )
    retired_count = track_count_result.scalar() or 0

    # Retire tracks (logical delete)
    await session.execute(
        update(Track)
        .where(Track.channel_id == channel.id)
        .values(is_retired=True)
    )

    # Cancel pending requests
    await session.execute(
        update(Request)
        .where(Request.channel_id == channel.id, Request.status == "pending")
        .values(status="cancelled")
    )

    # Delete now_playing record
    np_result = await session.execute(
        select(NowPlaying).where(NowPlaying.channel_id == channel.id)
    )
    np = np_result.scalar_one_or_none()
    if np:
        await session.delete(np)

    # Logical delete channel
    channel.is_active = False
    await session.commit()

    return {"ok": True, "deleted_tracks": retired_count}
