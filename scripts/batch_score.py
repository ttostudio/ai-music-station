"""バッチ品質スコアリングスクリプト

未スコア曲（quality_score IS NULL）を並行5で処理する。

使い方:
    docker exec product-ai-music-station-api-1 python -m scripts.batch_score
    docker exec product-ai-music-station-api-1 python -m scripts.batch_score --dry-run
    docker exec product-ai-music-station-api-1 python -m scripts.batch_score --concurrency 3
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from worker.models import Channel, Track
from worker.quality_scorer import QualityScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

TRACKS_MOUNT = "/tracks"
DEFAULT_CONCURRENCY = 5


async def _score_one(
    session_factory: async_sessionmaker,
    track_id,
    file_path: str,
    channel_threshold: float,
    scorer: QualityScorer,
    dry_run: bool,
) -> bool:
    """1トラックをスコアリングして成否を返す。"""
    if dry_run:
        logger.info("[dry-run] would score track %s (%s)", track_id, file_path)
        return True
    async with session_factory() as session:
        try:
            await scorer.score_track(
                session=session,
                track_id=track_id,
                file_path=file_path,
                channel_threshold=channel_threshold,
            )
            await session.commit()
            return True
        except Exception:
            logger.exception("スコアリング失敗: track_id=%s", track_id)
            await session.rollback()
            return False


async def main(dry_run: bool, concurrency: int) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL が設定されていません")
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # 未スコアトラックを取得
    async with session_factory() as session:
        result = await session.execute(
            select(Track).where(Track.quality_score.is_(None))
        )
        tracks = list(result.scalars().all())

    total = len(tracks)
    if total == 0:
        logger.info("未スコアのトラックはありません")
        return

    logger.info(
        "未スコアトラック: %d 件 (dry_run=%s, concurrency=%d)",
        total, dry_run, concurrency,
    )

    scorer = QualityScorer()
    sem = asyncio.Semaphore(concurrency)
    processed = 0
    succeeded = 0
    failed = 0
    lock = asyncio.Lock()

    async def bounded_score(track: Track) -> None:
        nonlocal processed, succeeded, failed

        async with session_factory() as s:
            ch = await s.get(Channel, track.channel_id)
            threshold = ch.quality_threshold if ch else 30.0

        file_path = f"{TRACKS_MOUNT}/{track.file_path}"

        async with sem:
            ok = await _score_one(
                session_factory, track.id, file_path, threshold, scorer, dry_run
            )
            async with lock:
                processed += 1
                if ok:
                    succeeded += 1
                else:
                    failed += 1
                logger.info(
                    "[%d/%d] track=%s score=%s",
                    processed, total, track.id, "OK" if ok else "FAIL",
                )

    await asyncio.gather(*[bounded_score(t) for t in tracks])

    logger.info(
        "完了: total=%d succeeded=%d failed=%d",
        total, succeeded, failed,
    )
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="バッチ品質スコアリング")
    parser.add_argument("--dry-run", action="store_true", help="実際にはスコアリングしない")
    parser.add_argument(
        "--concurrency", type=int, default=DEFAULT_CONCURRENCY,
        help=f"並行数 (デフォルト: {DEFAULT_CONCURRENCY})",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, concurrency=args.concurrency))
