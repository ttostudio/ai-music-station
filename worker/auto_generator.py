"""チャンネル自動生成ジョブ — 在庫不足チャンネルにリクエストを自動補充する"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import psutil
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.config import settings
from worker.lyrics_generator import LyricsGenerator
from worker.models import Channel, Request, Track
from worker.playlist_generator import generate_weighted_playlist
from worker.preference_analyzer import analyze_channel_preferences
from worker.track_retirement import cleanup_excess_tracks

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


async def get_existing_titles(
    session: AsyncSession, channel_id: uuid.UUID, limit: int = 50,
) -> list[str]:
    """チャンネルの既存トラックタイトル一覧を取得する（重複防止用）。"""
    result = await session.execute(
        select(Track.title)
        .where(
            Track.channel_id == channel_id,
            Track.is_retired == False,  # noqa: E712
            Track.title.isnot(None),
        )
        .order_by(Track.created_at.desc())
        .limit(limit)
    )
    return [row[0] for row in result.all()]


async def create_auto_request(
    session: AsyncSession, channel: Channel,
) -> Request:
    """嗜好分析と歌詞生成を組み合わせて自動リクエストを作成する。"""
    profile = await analyze_channel_preferences(session, channel.id)

    mood = channel.mood_description or channel.name
    if profile.prompt_hint:
        mood = f"{mood} ({profile.prompt_hint})"

    # 既存タイトルを取得して重複を防止
    existing_titles = await get_existing_titles(session, channel.id)

    generator = LyricsGenerator()
    lyrics_result = await generator.generate(
        mood=mood,
        channel_name=channel.name,
        channel_description=channel.description,
        existing_titles=existing_titles,
    )

    caption = lyrics_result.caption
    if lyrics_result.title:
        caption = f"{lyrics_result.title} | {caption}"

    request = Request(
        id=uuid.uuid4(),
        channel_id=channel.id,
        status="pending",
        mood=mood,
        caption=caption,
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
        # 全アクティブチャンネルを取得（棚卸しは auto_generate に関係なく実行）
        all_result = await session.execute(
            select(Channel).where(
                Channel.is_active == True,  # noqa: E712
            )
        )
        all_channels = all_result.scalars().all()

        # 棚卸し: max_stock超過時に不人気曲を退役+FLAC削除
        for channel in all_channels:
            try:
                retired = await cleanup_excess_tracks(
                    session,
                    channel.id,
                    channel.slug,
                    channel.max_stock,
                    settings.generated_tracks_dir,
                )
                if retired > 0:
                    await generate_weighted_playlist(
                        session, channel.id, channel.slug,
                        settings.generated_tracks_dir,
                        playlist_tracks_dir=settings.liquidsoap_tracks_dir,
                    )
            except Exception:
                logger.exception(
                    "channel=%s: 棚卸し処理失敗", channel.slug,
                )

        # 自動生成: auto_generate が有効なチャンネルの在庫不足率を計算
        channel_stocks = []
        for channel in all_channels:
            if not channel.auto_generate:
                continue

            pending = await get_pending_request_count(session, channel.id)
            if pending > 0:
                logger.debug(
                    "channel=%s: 処理待ちリクエストあり(%d件)、スキップ",
                    channel.slug, pending,
                )
                continue

            stock = await get_active_stock(session, channel.id)
            deficit = channel.min_stock - stock  # 正の値 = 不足
            channel_stocks.append((channel, stock, deficit))

        # 不足が多い順にソート（均等化のため）
        channel_stocks.sort(key=lambda x: x[2], reverse=True)

        # 1サイクルで最大1曲のみ生成（ラウンドロビン）
        for channel, stock, deficit in channel_stocks:
            if deficit <= 0:
                logger.debug(
                    "channel=%s: 在庫十分(%d/%d)、スキップ",
                    channel.slug, stock, channel.min_stock,
                )
                continue

            logger.info(
                "channel=%s: 在庫不足(%d/%d, 不足%d曲)、自動生成開始",
                channel.slug, stock, channel.min_stock, deficit,
            )
            try:
                await create_auto_request(session, channel)
                created += 1
                break  # 1サイクル1曲で次のサイクルに回す
            except Exception:
                logger.exception(
                    "channel=%s: 自動リクエスト作成失敗", channel.slug,
                )

    logger.info("自動生成完了: %d件作成", created)
    return created
