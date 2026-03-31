"""bossanova/classical/electronic チャンネル無音問題修正スクリプト

Step 1: ファントムレコード退役
    （DBレコードはあるがファイルが存在しないものを is_retired=true に更新）
Step 2: クロスチャンネル再配置（jazz→bossanova, game→classical, egushugi+lofi→electronic）
Step 3: playlist.m3u 更新

使い方:
    docker exec product-ai-music-station-api-1 python -m scripts.fix_empty_channels
    docker exec product-ai-music-station-api-1 python -m scripts.fix_empty_channels --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import shutil
import uuid
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from worker.models import Channel, Track

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

TRACKS_MOUNT = "/tracks"

# クロスチャンネル再配置マッピング: {target_slug: [(source_slug, count), ...]}
CHANNEL_MAPPING: dict[str, list[tuple[str, int]]] = {
    "bossanova": [("jazz", 10)],
    "classical": [("game", 10)],
    "electronic": [("egushugi", 5), ("lofi", 5)],
}

# 再配置完了後に auto_generate を false に設定するチャンネル（ACE-Step 停止中のため）
AUTO_GENERATE_OFF = ["bossanova", "classical", "electronic"]


async def retire_phantom_records(
    session_factory: async_sessionmaker,
    target_slugs: list[str],
    tracks_dir: Path,
    dry_run: bool,
) -> dict[str, list[uuid.UUID]]:
    """ファントムレコードを is_retired=true に更新する。

    Returns: {slug: [retired_track_ids]}
    """
    retired: dict[str, list[uuid.UUID]] = {}

    async with session_factory() as session:
        # 対象チャンネルを取得
        result = await session.execute(
            select(Channel).where(Channel.slug.in_(target_slugs))
        )
        channels = {ch.slug: ch for ch in result.scalars().all()}

        for slug in target_slugs:
            channel = channels.get(slug)
            if not channel:
                logger.warning("チャンネルが見つかりません: %s", slug)
                continue

            # is_retired=false のトラックを全て取得
            result = await session.execute(
                select(Track).where(
                    Track.channel_id == channel.id,
                    Track.is_retired == False,  # noqa: E712
                )
            )
            tracks = result.scalars().all()

            phantom_ids: list[uuid.UUID] = []
            for track in tracks:
                file_path = tracks_dir / track.file_path
                if not file_path.exists():
                    phantom_ids.append(track.id)
                    logger.info(
                        "[%s] ファントムレコード検出: %s (file_path=%s)",
                        slug, track.id, track.file_path,
                    )

            retired[slug] = phantom_ids
            logger.info("[%s] ファントムレコード: %d 件", slug, len(phantom_ids))

            if phantom_ids and not dry_run:
                await session.execute(
                    update(Track)
                    .where(Track.id.in_(phantom_ids))
                    .values(is_retired=True)
                )
                await session.commit()
                logger.info("[%s] %d 件を is_retired=true に更新", slug, len(phantom_ids))
            elif phantom_ids and dry_run:
                logger.info("[dry-run] %d 件を is_retired=true にする予定", len(phantom_ids))

    return retired


async def relocate_tracks(
    session_factory: async_sessionmaker,
    channel_mapping: dict[str, list[tuple[str, int]]],
    tracks_dir: Path,
    dry_run: bool,
) -> dict[str, int]:
    """クロスチャンネル再配置を実行する。

    Returns: {target_slug: copied_count}
    """
    copied_counts: dict[str, int] = {}

    async with session_factory() as session:
        # 全チャンネルを slug→channel マップで取得
        all_slugs = list(channel_mapping.keys()) + [
            s for sources in channel_mapping.values() for s, _ in sources
        ]
        result = await session.execute(
            select(Channel).where(Channel.slug.in_(all_slugs))
        )
        channels = {ch.slug: ch for ch in result.scalars().all()}

        for target_slug, sources in channel_mapping.items():
            target_channel = channels.get(target_slug)
            if not target_channel:
                logger.warning("ターゲットチャンネルが見つかりません: %s", target_slug)
                continue

            target_dir = tracks_dir / target_slug
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            total_copied = 0

            for source_slug, count in sources:
                source_channel = channels.get(source_slug)
                if not source_channel:
                    logger.warning("ソースチャンネルが見つかりません: %s", source_slug)
                    continue

                # ソースチャンネルから is_retired=false かつファイル存在するトラックを取得
                result = await session.execute(
                    select(Track).where(
                        Track.channel_id == source_channel.id,
                        Track.is_retired == False,  # noqa: E712
                    )
                )
                source_tracks = result.scalars().all()

                # ファイルが実在するトラックのみ
                available = [
                    t for t in source_tracks
                    if (tracks_dir / t.file_path).exists()
                ]

                if len(available) < count:
                    logger.warning(
                        "[%s] ソース %s から %d 曲要求だが %d 曲しか利用可能",
                        target_slug, source_slug, count, len(available),
                    )
                    count = len(available)

                selected = random.sample(available, count)
                logger.info(
                    "[%s] ソース %s から %d 曲を選定",
                    target_slug, source_slug, len(selected),
                )

                for source_track in selected:
                    new_track_id = uuid.uuid4()
                    src_file = tracks_dir / source_track.file_path
                    # 拡張子を維持
                    ext = src_file.suffix
                    new_file_path = f"{target_slug}/{new_track_id}{ext}"
                    dst_file = tracks_dir / new_file_path

                    logger.info(
                        "[%s] コピー: %s → %s",
                        target_slug, src_file, dst_file,
                    )

                    if not dry_run:
                        shutil.copy2(src_file, dst_file)

                        # 新規 DB レコード作成
                        new_track = Track(
                            id=new_track_id,
                            channel_id=target_channel.id,
                            file_path=new_file_path,
                            file_size=source_track.file_size,
                            duration_ms=source_track.duration_ms,
                            sample_rate=source_track.sample_rate,
                            title=source_track.title,
                            mood=source_track.mood,
                            caption=source_track.caption,
                            lyrics=source_track.lyrics,
                            bpm=source_track.bpm,
                            music_key=source_track.music_key,
                            instrumental=source_track.instrumental,
                            quality_score=source_track.quality_score,
                            generation_model="cross-channel-reuse",
                            is_retired=False,
                            play_count=0,
                            like_count=0,
                        )
                        session.add(new_track)
                        total_copied += 1
                    else:
                        logger.info("[dry-run] %s にコピー予定", new_file_path)
                        total_copied += 1

                if not dry_run:
                    await session.commit()

            copied_counts[target_slug] = total_copied
            logger.info("[%s] %d 曲を再配置", target_slug, total_copied)

    return copied_counts


async def update_playlists(
    session_factory: async_sessionmaker,
    target_slugs: list[str],
    tracks_dir: Path,
    liquidsoap_tracks_dir: str,
    dry_run: bool,
) -> dict[str, int]:
    """各チャンネルの playlist.m3u を更新する。

    Returns: {slug: track_count}
    """
    from worker.playlist_generator import generate_weighted_playlist

    counts: dict[str, int] = {}

    async with session_factory() as session:
        result = await session.execute(
            select(Channel).where(Channel.slug.in_(target_slugs))
        )
        channels = {ch.slug: ch for ch in result.scalars().all()}

        for slug in target_slugs:
            channel = channels.get(slug)
            if not channel:
                continue

            if dry_run:
                # dry-run: ファイル存在するトラック数のみカウント
                result2 = await session.execute(
                    select(Track).where(
                        Track.channel_id == channel.id,
                        Track.is_retired == False,  # noqa: E712
                    )
                )
                tracks = result2.scalars().all()
                cnt = sum(1 for t in tracks if (tracks_dir / t.file_path).exists())
                logger.info("[dry-run] [%s] playlist.m3u: %d トラック", slug, cnt)
                counts[slug] = cnt
            else:
                cnt = await generate_weighted_playlist(
                    session=session,
                    channel_id=channel.id,
                    channel_slug=slug,
                    tracks_dir=str(tracks_dir),
                    playlist_tracks_dir=liquidsoap_tracks_dir,
                )
                counts[slug] = cnt
                logger.info("[%s] playlist.m3u を更新: %d トラック", slug, cnt)

    return counts


async def disable_auto_generate(
    session_factory: async_sessionmaker,
    target_slugs: list[str],
    dry_run: bool,
) -> None:
    """ACE-Step 停止中のため auto_generate=false に設定する（Minor-002 対応）。"""
    async with session_factory() as session:
        result = await session.execute(
            select(Channel).where(Channel.slug.in_(target_slugs))
        )
        channels = result.scalars().all()

        for channel in channels:
            if dry_run:
                logger.info(
                    "[dry-run] [%s] auto_generate を false に設定予定", channel.slug
                )
            else:
                channel.auto_generate = False
                logger.info("[%s] auto_generate=false に設定", channel.slug)

        if not dry_run:
            await session.commit()


async def main(dry_run: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL 環境変数が設定されていません")

    tracks_dir = Path(TRACKS_MOUNT)
    liquidsoap_tracks_dir = TRACKS_MOUNT
    target_slugs = list(CHANNEL_MAPPING.keys())

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        logger.info("=" * 60)
        logger.info("無音チャンネル修正スクリプト開始 (dry_run=%s)", dry_run)
        logger.info("=" * 60)

        # Step 1: ファントムレコード退役
        logger.info("--- Step 1: ファントムレコード退役 ---")
        retired = await retire_phantom_records(
            session_factory, target_slugs, tracks_dir, dry_run
        )
        total_retired = sum(len(ids) for ids in retired.values())
        logger.info("ファントムレコード退役合計: %d 件", total_retired)

        # Step 2: クロスチャンネル再配置
        logger.info("--- Step 2: クロスチャンネル再配置 ---")
        copied = await relocate_tracks(
            session_factory, CHANNEL_MAPPING, tracks_dir, dry_run
        )
        total_copied = sum(copied.values())
        logger.info("再配置合計: %d 曲", total_copied)

        # Step 3: playlist.m3u 更新
        logger.info("--- Step 3: playlist.m3u 更新 ---")
        playlist_counts = await update_playlists(
            session_factory, target_slugs, tracks_dir, liquidsoap_tracks_dir, dry_run
        )

        # Step 4: auto_generate 無効化（Minor-002 対応）
        logger.info("--- Step 4: auto_generate 無効化 ---")
        await disable_auto_generate(session_factory, AUTO_GENERATE_OFF, dry_run)

        # サマリー
        logger.info("=" * 60)
        logger.info("完了サマリー (dry_run=%s)", dry_run)
        logger.info("  ファントムレコード退役: %d 件", total_retired)
        logger.info("  再配置:")
        for slug, cnt in copied.items():
            logger.info("    %s: %d 曲", slug, cnt)
        logger.info("  playlist.m3u:")
        for slug, cnt in playlist_counts.items():
            logger.info("    %s: %d トラック", slug, cnt)
        logger.info("=" * 60)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="無音チャンネル修正スクリプト")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の変更を行わずに動作確認のみ実行",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
