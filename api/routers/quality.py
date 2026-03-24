"""トラック品質スコア API ルーター"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import (
    ChannelQualityStatsResponse,
    QualityScoreListResponse,
    QualityThresholdUpdateRequest,
    QualityThresholdUpdateResponse,
    TrackQualityResponse,
)
from worker.models import Channel, Track, TrackQualityScore
from worker.quality_scorer import QualityScorer

router = APIRouter(tags=["quality"])


def _build_quality_response(
    qs: TrackQualityScore,
) -> TrackQualityResponse:
    return TrackQualityResponse(
        track_id=qs.track_id,
        score=qs.score,
        auto_drafted=qs.auto_drafted,
        duration_sec=qs.duration_sec,
        bit_rate=qs.bit_rate,
        sample_rate=qs.sample_rate,
        mean_volume_db=qs.mean_volume_db,
        max_volume_db=qs.max_volume_db,
        silence_ratio=qs.silence_ratio,
        dynamic_range_db=qs.dynamic_range_db,
        score_breakdown=qs.score_details or {},
        scored_at=qs.created_at,
    )


@router.get("/api/tracks/{track_id}/quality")
async def get_track_quality(
    track_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> TrackQualityResponse:
    result = await session.execute(
        select(TrackQualityScore)
        .where(TrackQualityScore.track_id == track_id)
        .order_by(TrackQualityScore.created_at.desc())
        .limit(1)
    )
    qs = result.scalar_one_or_none()
    if qs is None:
        raise HTTPException(status_code=404, detail="Quality score not found")
    return _build_quality_response(qs)


@router.post("/api/tracks/{track_id}/quality/rescore")
async def rescore_track(
    track_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> TrackQualityResponse:
    track = await session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")

    # チャンネルの閾値を取得
    channel = await session.get(Channel, track.channel_id)
    threshold = channel.quality_threshold if channel else 30.0

    scorer = QualityScorer()
    quality_record = await scorer.score_track(
        session=session,
        track_id=track_id,
        file_path=track.file_path,
        channel_threshold=threshold,
    )
    await session.commit()
    return _build_quality_response(quality_record)


@router.get("/api/channels/{slug}/quality/stats")
async def get_channel_quality_stats(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> ChannelQualityStatsResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    # スコア済みトラック統計
    stats_result = await session.execute(
        select(
            func.count(Track.id),
            func.avg(Track.quality_score),
        )
        .where(
            Track.channel_id == channel.id,
            Track.quality_score.is_not(None),
        )
    )
    row = stats_result.one()
    total_scored = row[0] or 0
    avg_score = round(float(row[1] or 0), 1)

    # 自動ドラフト数
    drafted_result = await session.execute(
        select(func.count(TrackQualityScore.id)).where(
            TrackQualityScore.track_id.in_(
                select(Track.id).where(Track.channel_id == channel.id)
            ),
            TrackQualityScore.auto_drafted.is_(True),
        )
    )
    auto_drafted_count = drafted_result.scalar() or 0

    # スコア分布
    distribution: dict[str, int] = {
        "0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0,
    }
    dist_result = await session.execute(
        select(Track.quality_score)
        .where(
            Track.channel_id == channel.id,
            Track.quality_score.is_not(None),
        )
    )
    for (s,) in dist_result.all():
        if s < 20:
            distribution["0-20"] += 1
        elif s < 40:
            distribution["20-40"] += 1
        elif s < 60:
            distribution["40-60"] += 1
        elif s < 80:
            distribution["60-80"] += 1
        else:
            distribution["80-100"] += 1

    # 直近10件
    recent_result = await session.execute(
        select(TrackQualityScore)
        .where(
            TrackQualityScore.track_id.in_(
                select(Track.id).where(Track.channel_id == channel.id)
            )
        )
        .order_by(TrackQualityScore.created_at.desc())
        .limit(10)
    )
    recent_scores = [
        _build_quality_response(qs)
        for qs in recent_result.scalars().all()
    ]

    return ChannelQualityStatsResponse(
        channel_slug=slug,
        threshold=channel.quality_threshold,
        total_scored=total_scored,
        avg_score=avg_score,
        auto_drafted_count=auto_drafted_count,
        score_distribution=distribution,
        recent_scores=recent_scores,
    )


@router.patch("/api/channels/{slug}/quality/threshold")
async def update_channel_threshold(
    slug: str,
    body: QualityThresholdUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> QualityThresholdUpdateResponse:
    result = await session.execute(
        select(Channel).where(Channel.slug == slug)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    await session.execute(
        update(Channel)
        .where(Channel.id == channel.id)
        .values(quality_threshold=body.threshold)
    )
    await session.commit()

    return QualityThresholdUpdateResponse(
        channel_slug=slug,
        threshold=body.threshold,
    )


@router.get("/api/quality/scores")
async def list_quality_scores(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    channel: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> QualityScoreListResponse:
    base_query = (
        select(TrackQualityScore)
        .join(Track, TrackQualityScore.track_id == Track.id)
    )
    count_query = (
        select(func.count(TrackQualityScore.id))
        .select_from(TrackQualityScore)
        .join(Track, TrackQualityScore.track_id == Track.id)
    )

    if channel:
        ch_result = await session.execute(
            select(Channel.id).where(Channel.slug == channel)
        )
        ch_id = ch_result.scalar_one_or_none()
        if ch_id is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        base_query = base_query.where(Track.channel_id == ch_id)
        count_query = count_query.where(Track.channel_id == ch_id)

    # 集計
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    avg_result = await session.execute(
        select(func.avg(Track.quality_score)).where(
            Track.quality_score.is_not(None)
        )
    )
    avg_score = round(float(avg_result.scalar() or 0), 1)

    drafted_result = await session.execute(
        select(func.count(TrackQualityScore.id)).where(
            TrackQualityScore.auto_drafted.is_(True)
        )
    )
    auto_drafted_count = drafted_result.scalar() or 0

    # ページネーション
    items_result = await session.execute(
        base_query
        .order_by(TrackQualityScore.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        _build_quality_response(qs)
        for qs in items_result.scalars().all()
    ]

    return QualityScoreListResponse(
        total=total,
        avg_score=avg_score,
        auto_drafted_count=auto_drafted_count,
        items=items,
    )
