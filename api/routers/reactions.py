"""リアクション（👍）API — トラックへのフィードバック管理"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import ReactionBody, ReactionResponse, ReactionStatusResponse
from worker.models import Reaction, Track

router = APIRouter(prefix="/api/tracks/{track_id}", tags=["reactions"])


@router.post("/reactions", response_model=ReactionResponse)
async def add_reaction(
    track_id: str,
    body: ReactionBody,
    session: AsyncSession = Depends(get_session),
) -> ReactionResponse:
    """トラックにリアクションを追加する"""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="トラックが見つかりません")

    reaction = Reaction(
        track_id=track.id,
        session_id=body.session_id,
        reaction_type=body.reaction_type,
    )
    session.add(reaction)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="すでにリアクション済みです"
        ) from None

    # like_count をアトミックに更新
    await session.execute(
        update(Track)
        .where(Track.id == track.id)
        .values(like_count=Track.like_count + 1)
    )
    await session.commit()
    await session.refresh(track)
    return ReactionResponse(ok=True, count=track.like_count)


@router.delete("/reactions", response_model=ReactionResponse)
async def remove_reaction(
    track_id: str,
    body: ReactionBody,
    session: AsyncSession = Depends(get_session),
) -> ReactionResponse:
    """トラックのリアクションを削除する"""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="トラックが見つかりません")

    result = await session.execute(
        delete(Reaction).where(
            Reaction.track_id == track.id,
            Reaction.session_id == body.session_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="リアクションが見つかりません")

    # like_count をアトミックに更新（0未満にならないようガード）
    await session.execute(
        update(Track)
        .where(Track.id == track.id)
        .values(like_count=func.greatest(Track.like_count - 1, 0))
    )
    await session.commit()
    await session.refresh(track)
    return ReactionResponse(ok=True, count=track.like_count)


@router.get("/reactions", response_model=ReactionStatusResponse)
async def get_reaction_status(
    track_id: str,
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> ReactionStatusResponse:
    """トラックのリアクション状態を取得する"""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="トラックが見つかりません")

    # ユーザーのリアクション有無
    user_result = await session.execute(
        select(func.count()).select_from(Reaction).where(
            Reaction.track_id == track.id,
            Reaction.session_id == session_id,
        )
    )
    user_reacted = (user_result.scalar() or 0) > 0

    return ReactionStatusResponse(count=track.like_count, user_reacted=user_reacted)
