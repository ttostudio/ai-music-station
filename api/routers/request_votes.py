"""リクエスト投票 API — pending リクエストへの投票管理"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import RequestVoteBody, RequestVoteResponse, RequestVoteStatusResponse
from worker.models import Request, RequestVote

router = APIRouter(prefix="/api/requests/{request_id}", tags=["request_votes"])


@router.post("/votes", response_model=RequestVoteResponse)
async def add_vote(
    request_id: uuid.UUID,
    body: RequestVoteBody,
    session: AsyncSession = Depends(get_session),
) -> RequestVoteResponse:
    """リクエストに投票する"""
    req = await session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")

    vote = RequestVote(
        request_id=req.id,
        session_id=body.session_id,
    )
    session.add(vote)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="すでに投票済みです"
        ) from None

    await session.execute(
        update(Request)
        .where(Request.id == req.id)
        .values(vote_count=Request.vote_count + 1)
    )
    await session.commit()
    await session.refresh(req)
    return RequestVoteResponse(ok=True, count=req.vote_count)


@router.delete("/votes", response_model=RequestVoteResponse)
async def remove_vote(
    request_id: uuid.UUID,
    body: RequestVoteBody,
    session: AsyncSession = Depends(get_session),
) -> RequestVoteResponse:
    """リクエストへの投票を取り消す"""
    req = await session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")

    result = await session.execute(
        delete(RequestVote).where(
            RequestVote.request_id == req.id,
            RequestVote.session_id == body.session_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="投票が見つかりません")

    await session.execute(
        update(Request)
        .where(Request.id == req.id)
        .values(vote_count=func.greatest(Request.vote_count - 1, 0))
    )
    await session.commit()
    await session.refresh(req)
    return RequestVoteResponse(ok=True, count=req.vote_count)


@router.get("/votes", response_model=RequestVoteStatusResponse)
async def get_vote_status(
    request_id: uuid.UUID,
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> RequestVoteStatusResponse:
    """リクエストへの投票状態を取得する"""
    req = await session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")

    user_result = await session.execute(
        select(func.count()).select_from(RequestVote).where(
            RequestVote.request_id == req.id,
            RequestVote.session_id == session_id,
        )
    )
    user_voted = (user_result.scalar() or 0) > 0

    return RequestVoteStatusResponse(count=req.vote_count, user_voted=user_voted)
