from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_session
from api.schemas import (
    CreateRequestBody,
    RequestDetailResponse,
    RequestListResponse,
    RequestResponse,
    TrackResponse,
)
from worker.lyrics_generator import LyricsGenerator
from worker.models import Channel, Request, Track

logger = logging.getLogger(__name__)

router = APIRouter(tags=["requests"])


@router.post(
    "/api/channels/{slug}/requests",
    response_model=RequestResponse,
    status_code=201,
)
async def create_request(
    slug: str,
    body: CreateRequestBody,
    session: AsyncSession = Depends(get_session),
) -> RequestResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    caption = body.caption
    lyrics = body.lyrics
    mood = body.mood

    # mood指定時: claude CLIで歌詞・曲名・キャプションを自動生成
    if mood:
        try:
            generator = LyricsGenerator(
                claude_command=settings.claude_command,
            )
            gen_result = await generator.generate(
                mood=mood,
                channel_name=channel.name,
                channel_description=channel.description,
            )
            generated_title = gen_result.title
            caption = caption or gen_result.caption
            if generated_title:
                caption = f"{generated_title} | {caption}"
            lyrics = lyrics or gen_result.lyrics
        except Exception:
            logger.warning(
                "歌詞自動生成に失敗しました（ユーザー入力を使用）",
                exc_info=True,
            )

    req = Request(
        channel_id=channel.id,
        mood=mood,
        caption=caption,
        lyrics=lyrics,
        bpm=body.bpm,
        duration=body.duration,
        music_key=body.music_key,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)

    pos_result = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(
            Request.channel_id == channel.id,
            Request.status == "pending",
            Request.created_at <= req.created_at,
        )
    )
    position = pos_result.scalar() or 1

    return RequestResponse(
        id=req.id,
        channel_slug=slug,
        status=req.status,
        position=position,
        created_at=req.created_at,
    )


@router.get(
    "/api/channels/{slug}/requests",
    response_model=RequestListResponse,
)
async def list_requests(
    slug: str,
    status: str = Query("pending"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> RequestListResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    query = (
        select(Request)
        .where(Request.channel_id == channel.id, Request.status == status)
        .order_by(Request.created_at)
        .offset(offset)
        .limit(limit)
    )
    rows = await session.execute(query)
    requests = rows.scalars().all()

    count_result = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(Request.channel_id == channel.id, Request.status == status)
    )
    total = count_result.scalar() or 0

    items = []
    for r in requests:
        track = None
        if r.status == "completed":
            track_row = await session.execute(
                select(Track).where(Track.request_id == r.id)
            )
            t = track_row.scalar_one_or_none()
            if t:
                track = TrackResponse(
                    id=t.id,
                    caption=t.caption,
                    duration_ms=t.duration_ms,
                    bpm=t.bpm,
                    music_key=t.music_key,
                    instrumental=t.instrumental,
                    play_count=t.play_count,
                    created_at=t.created_at,
                )
        items.append(
            RequestDetailResponse(
                id=r.id,
                channel_slug=slug,
                status=r.status,
                mood=r.mood,
                caption=r.caption,
                lyrics=r.lyrics,
                bpm=r.bpm,
                duration=r.duration,
                music_key=r.music_key,
                vote_count=r.vote_count,
                created_at=r.created_at,
                started_at=r.started_at,
                completed_at=r.completed_at,
                error_message=r.error_message,
                track=track,
            )
        )

    return RequestListResponse(requests=items, total=total)


@router.get("/api/requests", response_model=RequestListResponse)
async def list_all_requests(
    status: str = Query("pending,processing"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> RequestListResponse:
    valid_statuses = {"pending", "processing", "completed", "failed"}
    statuses = [s.strip() for s in status.split(",") if s.strip() in valid_statuses]
    if not statuses:
        statuses = list(valid_statuses)

    query = (
        select(Request, Channel)
        .join(Channel, Request.channel_id == Channel.id)
        .where(Request.status.in_(statuses))
        .order_by(Request.created_at.desc())
    )

    count_result = await session.execute(
        select(func.count()).select_from(
            select(Request)
            .where(Request.status.in_(statuses))
            .subquery()
        )
    )
    total = count_result.scalar() or 0

    rows = await session.execute(query.offset(offset).limit(limit))
    results = rows.all()

    items = []
    for req, channel in results:
        track = None
        if req.status == "completed":
            track_row = await session.execute(
                select(Track).where(Track.request_id == req.id)
            )
            t = track_row.scalar_one_or_none()
            if t:
                track = TrackResponse(
                    id=t.id,
                    caption=t.caption,
                    duration_ms=t.duration_ms,
                    bpm=t.bpm,
                    music_key=t.music_key,
                    instrumental=t.instrumental,
                    play_count=t.play_count,
                    created_at=t.created_at,
                )
        items.append(
            RequestDetailResponse(
                id=req.id,
                channel_slug=channel.slug,
                status=req.status,
                mood=req.mood,
                caption=req.caption,
                lyrics=req.lyrics,
                bpm=req.bpm,
                duration=req.duration,
                music_key=req.music_key,
                created_at=req.created_at,
                started_at=req.started_at,
                completed_at=req.completed_at,
                error_message=req.error_message,
                track=track,
            )
        )

    return RequestListResponse(requests=items, total=total)


@router.get("/api/requests/{request_id}", response_model=RequestDetailResponse)
async def get_request(
    request_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RequestDetailResponse:
    req = await session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")

    channel_result = await session.execute(
        select(Channel).where(Channel.id == req.channel_id)
    )
    channel = channel_result.scalar_one()

    track = None
    if req.status == "completed":
        track_row = await session.execute(
            select(Track).where(Track.request_id == req.id)
        )
        t = track_row.scalar_one_or_none()
        if t:
            track = TrackResponse(
                id=t.id,
                caption=t.caption,
                duration_ms=t.duration_ms,
                bpm=t.bpm,
                music_key=t.music_key,
                instrumental=t.instrumental,
                play_count=t.play_count,
                created_at=t.created_at,
            )

    position = None
    if req.status == "pending":
        pos_result = await session.execute(
            select(func.count())
            .select_from(Request)
            .where(
                Request.channel_id == req.channel_id,
                Request.status == "pending",
                Request.created_at <= req.created_at,
            )
        )
        position = pos_result.scalar()

    return RequestDetailResponse(
        id=req.id,
        channel_slug=channel.slug,
        status=req.status,
        mood=req.mood,
        caption=req.caption,
        lyrics=req.lyrics,
        bpm=req.bpm,
        duration=req.duration,
        music_key=req.music_key,
        position=position,
        vote_count=req.vote_count,
        created_at=req.created_at,
        started_at=req.started_at,
        completed_at=req.completed_at,
        error_message=req.error_message,
        track=track,
    )
