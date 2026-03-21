from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import HealthResponse
from worker.models import Channel

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "接続済み"
    except Exception:
        db_status = "未接続"

    result = await session.execute(
        select(func.count()).select_from(Channel).where(Channel.is_active.is_(True))
    )
    active = result.scalar() or 0

    return HealthResponse(
        status="正常" if db_status == "接続済み" else "低下",
        database=db_status,
        channels_active=active,
    )
