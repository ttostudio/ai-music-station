"""チャンネルヘルスチェックスクリプト

全チャンネルの DB トラック数とファイル数の不整合を検出する。

使い方:
    docker exec product-ai-music-station-api-1 python -m scripts.channel_health_check
    docker exec product-ai-music-station-api-1 \
        python -m scripts.channel_health_check --channel bossanova
    docker exec product-ai-music-station-api-1 \
        python -m scripts.channel_health_check --fail-on-mismatch
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from worker.models import Channel, Track

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

TRACKS_MOUNT = "/tracks"


@dataclass
class ChannelHealthReport:
    slug: str
    db_active: int          # is_retired=false のレコード数
    db_retired: int         # is_retired=true のレコード数
    file_count: int         # 実在ファイル数
    phantom_count: int      # DB にあるがファイルが存在しない
    orphan_count: int       # ファイルはあるが DB レコードが存在しない
    playlist_tracks: int    # playlist.m3u のエントリ数
    auto_generate: bool

    @property
    def is_healthy(self) -> bool:
        return self.phantom_count == 0 and self.db_active > 0 and self.playlist_tracks > 0

    @property
    def status(self) -> str:
        if self.db_active == 0:
            return "EMPTY"
        if self.phantom_count > 0:
            return "PHANTOM"
        if self.playlist_tracks == 0:
            return "NO_PLAYLIST"
        return "OK"


async def check_channel(
    session_factory: async_sessionmaker,
    channel: Channel,
    tracks_dir: Path,
) -> ChannelHealthReport:
    """1チャンネルのヘルスチェックを実行する。"""
    async with session_factory() as session:
        # アクティブトラック取得
        result = await session.execute(
            select(Track).where(
                Track.channel_id == channel.id,
                Track.is_retired == False,  # noqa: E712
            )
        )
        active_tracks = result.scalars().all()

        # 退役トラック数
        result_retired = await session.execute(
            select(Track).where(
                Track.channel_id == channel.id,
                Track.is_retired == True,  # noqa: E712
            )
        )
        retired_count = len(result_retired.scalars().all())

    channel_dir = tracks_dir / channel.slug
    channel_dir.mkdir(parents=True, exist_ok=True)

    # ファイル一覧（音声ファイルのみ）
    audio_extensions = {".flac", ".mp3", ".ogg", ".wav"}
    existing_files: set[str] = {
        f"{channel.slug}/{p.name}"
        for p in channel_dir.iterdir()
        if p.suffix.lower() in audio_extensions
    }

    # DB ファイルパス
    db_file_paths: set[str] = {t.file_path for t in active_tracks}

    # ファントム: DB にあるがファイルが存在しない
    phantom_paths = db_file_paths - existing_files
    # オーファン: ファイルはあるが DB にない
    orphan_paths = existing_files - db_file_paths

    # playlist.m3u エントリ数
    playlist_path = channel_dir / "playlist.m3u"
    playlist_tracks = 0
    if playlist_path.exists():
        lines = [
            line.strip()
            for line in playlist_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        playlist_tracks = len(lines)

    return ChannelHealthReport(
        slug=channel.slug,
        db_active=len(active_tracks),
        db_retired=retired_count,
        file_count=len(existing_files),
        phantom_count=len(phantom_paths),
        orphan_count=len(orphan_paths),
        playlist_tracks=playlist_tracks,
        auto_generate=channel.auto_generate,
    )


async def main(target_slugs: list[str] | None, fail_on_mismatch: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL 環境変数が設定されていません")

    tracks_dir = Path(TRACKS_MOUNT)

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            query = select(Channel).where(Channel.is_active == True)  # noqa: E712
            if target_slugs:
                query = query.where(Channel.slug.in_(target_slugs))
            result = await session.execute(query)
            channels = result.scalars().all()

        if not channels:
            logger.warning("チャンネルが見つかりません")
            return

        reports: list[ChannelHealthReport] = []
        for channel in sorted(channels, key=lambda c: c.slug):
            report = await check_channel(session_factory, channel, tracks_dir)
            reports.append(report)

        # レポート表示
        print("\n" + "=" * 72)
        header = (
            f"{'チャンネル':<16} {'状態':<12} {'DB(active)':<12}"
            f" {'ファイル':<10} {'ファントム':<10} {'プレイリスト':<12} {'自動生成'}"
        )
        print(header)
        print("-" * 72)
        has_issue = False
        for r in reports:
            flag = "" if r.is_healthy else " !"
            print(
                f"{r.slug:<16} {r.status:<12} {r.db_active:<12} {r.file_count:<10} "
                f"{r.phantom_count:<10} {r.playlist_tracks:<12} {str(r.auto_generate)}{flag}"
            )
            if not r.is_healthy:
                has_issue = True

        print("=" * 72)

        # 問題があるチャンネルの詳細
        problem_channels = [r for r in reports if not r.is_healthy]
        if problem_channels:
            print("\n問題のあるチャンネル:")
            for r in problem_channels:
                print(f"  [{r.slug}] status={r.status}")
                if r.db_active == 0:
                    print(f"    - アクティブトラックが 0 件（退役済み: {r.db_retired} 件）")
                if r.phantom_count > 0:
                    print(
                        f"    - ファントムレコード: {r.phantom_count} 件（DBにあるがファイルなし）"
                    )
                if r.playlist_tracks == 0:
                    print("    - playlist.m3u が空またはなし")
                if r.orphan_count > 0:
                    print(
                        f"    - オーファンファイル: {r.orphan_count} 件（ファイルはあるがDBになし）"
                    )
        else:
            print("\n全チャンネル正常です。")

        if fail_on_mismatch and has_issue:
            raise SystemExit(1)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="チャンネルヘルスチェックスクリプト")
    parser.add_argument(
        "--channel",
        nargs="+",
        metavar="SLUG",
        help="対象チャンネル slug（省略時は全チャンネル）",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="不整合があった場合に exit code 1 で終了（CI 連携用）",
    )
    args = parser.parse_args()
    asyncio.run(main(target_slugs=args.channel, fail_on_mismatch=args.fail_on_mismatch))
