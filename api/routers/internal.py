from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.schemas import NowPlayingUpdate, WorkerHeartbeat
from worker.models import Channel, NowPlaying, Track

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/now-playing")
async def update_now_playing(
    body: NowPlayingUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Channel).where(Channel.slug == body.channel_slug)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        return {"ok": False, "error": "チャンネルが見つかりません"}

    # 前のトラックの play_count をアトミックにインクリメント
    np = await session.get(NowPlaying, channel.id)
    if np and np.track_id and np.track_id != body.track_id:
        await session.execute(
            update(Track)
            .where(Track.id == np.track_id)
            .values(
                play_count=Track.play_count + 1,
                last_played_at=datetime.now(timezone.utc),
            )
        )

    if np:
        np.track_id = body.track_id
        np.started_at = datetime.now(timezone.utc)
    else:
        np = NowPlaying(
            channel_id=channel.id,
            track_id=body.track_id,
            started_at=datetime.now(timezone.utc),
        )
        session.add(np)
    await session.commit()
    return {"ok": True}


@router.post("/worker-heartbeat")
async def worker_heartbeat(body: WorkerHeartbeat) -> dict:
    return {"ok": True, "worker_id": body.worker_id}
