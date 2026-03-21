"""チャンネル自動生成ジョブ — 在庫不足チャンネルにリクエストを自動補充する"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import psutil
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.lyrics_generator import LyricsGenerator
from worker.models import Channel, Request, Track
from worker.preference_analyzer import analyze_channel_preferences

logger = logging.getLogger(__name__)

# システムリソース閾値
CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 85.0


def check_system_resources() -> bool:
    """システムリソースが十分かチェックする。

    Returns:
        True: リソースに余裕あり（生成可能）
        False: リソース不足（スキップすべき）
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    if cpu_percent > CPU_THRESHOLD:
        logger.info(
            "CPU使用率が閾値超過: %.1f%% > %.1f%%",
            cpu_percent, CPU_THRESHOLD,
        )
        return False
    if mem.percent > MEMORY_THRESHOLD:
        logger.info(
            "メモリ使用率が閾値超過: %.1f%% > %.1f%%",
            mem.percent, MEMORY_THRESHOLD,
        )
        return False
    return True


async def get_active_stock(
    session: AsyncSession, channel_id: uuid.UUID,
) -> int:
    """チャンネルの有効トラック数（未リタイア）を返す。"""
    result = await session.execute(
        select(func.count(Track.id)).where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
        )
    )
    return result.scalar() or 0


async def get_pending_request_count(
    session: AsyncSession, channel_id: uuid.UUID,
) -> int:
    """チャンネルの処理待ち/処理中リクエスト数を返す。"""
    result = await session.execute(
        select(func.count(Request.id)).where(
            Request.channel_id == channel_id,
            Request.status.in_(["pending", "processing"]),
        )
    )
    return result.scalar() or 0


async def create_auto_request(
    session: AsyncSession, channel: Channel,
) -> Request:
    """嗜好分析と歌詞生成を組み合わせて自動リクエストを作成する。"""
    profile = await analyze_channel_preferences(session, channel.id)

    mood = channel.mood_description or channel.name
    if profile.prompt_hint:
        mood = f"{mood} ({profile.prompt_hint})"

    generator = LyricsGenerator()
    lyrics_result = await generator.generate(
        mood=mood,
        channel_name=channel.name,
        channel_description=channel.description,
    )

    request = Request(
        id=uuid.uuid4(),
        channel_id=channel.id,
        status="pending",
        mood=mood,
        caption=lyrics_result.caption,
        lyrics=lyrics_result.lyrics if not channel.default_instrumental else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(request)
    await session.commit()

    logger.info(
        "自動リクエスト作成: channel=%s title='%s'",
        channel.slug, lyrics_result.title,
    )
    return request


async def run_auto_generation(session_factory) -> int:
    """全アクティブチャンネルの在庫を確認し、不足分を補充する。

    Returns:
        作成されたリクエスト数
    """
    if not check_system_resources():
        logger.info("システムリソース不足のため自動生成をスキップ")
        return 0

    created = 0
    async with session_factory() as session:
        result = await session.execute(
            select(Channel).where(
                Channel.is_active == True,  # noqa: E712
                Channel.auto_generate == True,  # noqa: E712
            )
        )
        channels = result.scalars().all()

        for channel in channels:
            pending = await get_pending_request_count(session, channel.id)
            if pending > 0:
                logger.debug(
                    "channel=%s: 処理待ちリクエストあり(%d件)、スキップ",
                    channel.slug, pending,
                )
                continue

            stock = await get_active_stock(session, channel.id)
            if stock >= channel.min_stock:
                logger.debug(
                    "channel=%s: 在庫十分(%d/%d)、スキップ",
                    channel.slug, stock, channel.min_stock,
                )
                continue

            logger.info(
                "channel=%s: 在庫不足(%d/%d)、自動生成開始",
                channel.slug, stock, channel.min_stock,
            )
            try:
                await create_auto_request(session, channel)
                created += 1
            except Exception:
                logger.exception(
                    "channel=%s: 自動リクエスト作成失敗", channel.slug,
                )

    logger.info("自動生成完了: %d件作成", created)
    return created
