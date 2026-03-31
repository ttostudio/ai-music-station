"""生成 API ルーター。

Endpoints:
    POST /api/generate                       — 生成リクエスト投入（チャンネル横断）
    GET  /api/generate/{request_id}/status   — 個別リクエストのステータス確認
    GET  /api/channels/{slug}/generate-status — チャンネル生成キュー状況
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import (
    GenerateRequestBody,
    GenerateStatusResponse,
    RequestDetailResponse,
    RequestResponse,
    TrackResponse,
)
from worker.models import Channel, Request, Track

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


@router.post(
    "/api/generate",
    response_model=RequestResponse,
    status_code=201,
)
async def create_generate_request(
    body: GenerateRequestBody,
    session: AsyncSession = Depends(get_session),
) -> RequestResponse:
    """生成リクエストを投入する。

    channel_slug を受け取り、対象チャンネルのキューに pending リクエストを追加する。
    """
    result = await session.execute(
        select(Channel).where(Channel.slug == body.channel_slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    # pending キューが max_stock を超えている場合は受け付けない
    pending_count_result = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(
            Request.channel_id == channel.id,
            Request.status.in_(["pending", "processing"]),
        )
    )
    pending_count = pending_count_result.scalar() or 0
    if pending_count >= channel.max_stock:
        raise HTTPException(
            status_code=429,
            detail=f"キューが満杯です（最大 {channel.max_stock} 件）",
        )

    req = Request(
        channel_id=channel.id,
        mood=body.mood,
        caption=body.caption,
        lyrics=body.lyrics,
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
        channel_slug=body.channel_slug,
        status=req.status,
        position=position,
        created_at=req.created_at,
    )


@router.get(
    "/api/generate/{request_id}/status",
    response_model=RequestDetailResponse,
)
async def get_generate_status(
    request_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RequestDetailResponse:
    """個別リクエストのステータスを返す。"""
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
        created_at=req.created_at,
        started_at=req.started_at,
        completed_at=req.completed_at,
        error_message=req.error_message,
        track=track,
    )


@router.get(
    "/api/channels/{slug}/generate-status",
    response_model=GenerateStatusResponse,
)
async def get_channel_generate_status(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> GenerateStatusResponse:
    """チャンネルの生成キュー状況を返す。

    stock_count: 利用可能なトラック数（退役・草稿化されていない）
    pending_count: pending 状態のリクエスト数
    processing_count: processing 状態のリクエスト数
    """
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

    stock_result = await session.execute(
        select(func.count())
        .select_from(Track)
        .where(
            Track.channel_id == channel.id,
            Track.is_retired == False,  # noqa: E712
        )
    )
    stock_count = stock_result.scalar() or 0

    pending_result = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(
            Request.channel_id == channel.id,
            Request.status == "pending",
        )
    )
    pending_count = pending_result.scalar() or 0

    processing_result = await session.execute(
        select(func.count())
        .select_from(Request)
        .where(
            Request.channel_id == channel.id,
            Request.status == "processing",
        )
    )
    processing_count = processing_result.scalar() or 0

    return GenerateStatusResponse(
        channel_slug=slug,
        stock_count=stock_count,
        pending_count=pending_count,
        processing_count=processing_count,
        min_stock=channel.min_stock,
        max_stock=channel.max_stock,
        auto_generate=channel.auto_generate,
    )
