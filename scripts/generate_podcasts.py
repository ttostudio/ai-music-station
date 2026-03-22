#!/usr/bin/env python3
"""ホスト側ポッドキャスト生成CLI

全未変換記事をポッドキャストに変換し、DBに登録する。
ワーカーと同様にホスト上で実行される（Edge TTS がホストにインストール済み）。

使用例:
    python3 scripts/generate_podcasts.py
    python3 scripts/generate_podcasts.py --slug claude-code-latest-features-guide
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from worker.config import settings
from worker.models import Channel, PodcastEpisode
from worker.podcast_generator import generate_all_episodes, generate_episode
from worker.playlist_generator import generate_podcast_playlist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("podcast-cli")


async def get_or_create_podcast_channel(session: AsyncSession) -> Channel:
    """podcast チャンネルを取得、なければ作成"""
    result = await session.execute(
        select(Channel).where(Channel.slug == "podcast")
    )
    channel = result.scalar_one_or_none()
    if channel:
        return channel

    channel = Channel(
        slug="podcast",
        name="AI Podcast",
        description="AI Tech Blog の記事を音声で配信するポッドキャストチャンネル",
        is_active=True,
        content_type="podcast",
        prompt_template="podcast",
        auto_generate=False,
        min_stock=0,
        max_stock=999,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    logger.info("podcast チャンネル作成: %s", channel.id)
    return channel


async def run_single(slug: str) -> None:
    """単一記事のポッドキャスト生成"""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 重複チェック
        existing = await session.execute(
            select(PodcastEpisode).where(PodcastEpisode.article_slug == slug)
        )
        if existing.scalar_one_or_none():
            logger.info("既にエピソード化済み: %s", slug)
            return

        channel = await get_or_create_podcast_channel(session)

        next_num_q = await session.execute(
            select(func.coalesce(func.max(PodcastEpisode.episode_number), 0) + 1)
        )
        next_num = next_num_q.scalar()

        ep_data = await generate_episode(slug, settings.generated_tracks_dir)

        episode = PodcastEpisode(
            channel_id=channel.id,
            article_id=ep_data.article_id,
            article_slug=ep_data.article_slug,
            title=ep_data.title,
            description=ep_data.description,
            audio_file_path=ep_data.audio_path,
            duration_ms=ep_data.duration_ms,
            episode_number=next_num,
        )
        session.add(episode)
        await session.commit()
        logger.info("エピソード生成完了: #%d %s", next_num, ep_data.title)

        # プレイリスト更新
        await generate_podcast_playlist(
            session, channel.id, channel.slug, settings.generated_tracks_dir,
        )

    await engine.dispose()


async def run_all() -> None:
    """全未変換記事のポッドキャスト生成"""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        channel = await get_or_create_podcast_channel(session)

        # 既存スラッグ
        existing_q = await session.execute(
            select(PodcastEpisode.article_slug)
        )
        existing_slugs = {row[0] for row in existing_q.all()}

        max_num_q = await session.execute(
            select(func.coalesce(func.max(PodcastEpisode.episode_number), 0))
        )
        next_num = (max_num_q.scalar() or 0) + 1

        episodes_data = await generate_all_episodes(
            settings.generated_tracks_dir, existing_slugs,
        )

        for ep_data in episodes_data:
            episode = PodcastEpisode(
                channel_id=channel.id,
                article_id=ep_data.article_id,
                article_slug=ep_data.article_slug,
                title=ep_data.title,
                description=ep_data.description,
                audio_file_path=ep_data.audio_path,
                duration_ms=ep_data.duration_ms,
                episode_number=next_num,
            )
            session.add(episode)
            next_num += 1

        await session.commit()
        logger.info("全エピソード生成完了: %d 件", len(episodes_data))

        # プレイリスト更新
        await generate_podcast_playlist(
            session, channel.id, channel.slug, settings.generated_tracks_dir,
        )

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Podcast 生成CLI")
    parser.add_argument(
        "--slug", type=str, default=None,
        help="特定の記事スラッグのみ生成（省略時は全未変換記事）",
    )
    args = parser.parse_args()

    if args.slug:
        asyncio.run(run_single(args.slug))
    else:
        asyncio.run(run_all())


if __name__ == "__main__":
    main()
