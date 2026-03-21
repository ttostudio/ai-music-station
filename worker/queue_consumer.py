from __future__ import annotations

import asyncio
import logging
import os
import platform
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from worker.acestep_client import ACEStepClient, GenerationError, GenerationParams
from worker.channel_presets import get_preset
from worker.config import settings
from worker.lyrics_generator import LyricsGenerator
from worker.models import Channel, Request, Track
from worker.playlist_generator import generate_weighted_playlist
from worker.track_retirement import retire_unpopular_tracks

logger = logging.getLogger(__name__)


class QueueConsumer:
    def __init__(
        self,
        session_factory,
        client: ACEStepClient | None = None,
        tracks_dir: str = settings.generated_tracks_dir,
        worker_id: str | None = None,
        lyrics_generator: LyricsGenerator | None = None,
    ):
        self.session_factory = session_factory
        self.client = client or ACEStepClient()
        self.tracks_dir = Path(tracks_dir)
        self.worker_id = worker_id or settings.worker_id or platform.node()
        if lyrics_generator:
            self.lyrics_generator = lyrics_generator
        elif settings.anthropic_api_key:
            self.lyrics_generator = LyricsGenerator(api_key=settings.anthropic_api_key)
        else:
            self.lyrics_generator = None

    async def claim_request(self, session: AsyncSession) -> Request | None:
        result = await session.execute(
            text(
                """
                UPDATE requests
                SET status = 'processing',
                    worker_id = :worker_id,
                    started_at = NOW(),
                    updated_at = NOW()
                WHERE id = (
                    SELECT id FROM requests
                    WHERE status = 'pending'
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING id
                """
            ),
            {"worker_id": self.worker_id},
        )
        row = result.fetchone()
        if row is None:
            return None

        request = await session.get(Request, row[0])
        await session.commit()
        return request

    def generate_lyrics(self, request: Request, channel: Channel) -> tuple[str, str, str]:
        """mood指定時にClaude APIで曲名・キャプション・歌詞を生成する。

        Returns:
            (title, caption, lyrics) のタプル
        """
        if not self.lyrics_generator:
            raise ValueError("ANTHROPIC_API_KEY が設定されていません")

        preset = get_preset(channel.slug)
        instrumental = preset.instrumental if preset else channel.default_instrumental
        prompt_template = preset.prompt_template if preset else channel.prompt_template

        result = self.lyrics_generator.generate(
            mood=request.mood,
            channel_name=channel.name,
            channel_description=channel.description or "",
            instrumental=instrumental,
            prompt_template=prompt_template,
        )
        return result.title, result.caption, result.lyrics

    def build_generation_params(
        self, request: Request, channel: Channel, *, generated_caption: str = "",
        generated_lyrics: str = "",
    ) -> GenerationParams:
        preset = get_preset(channel.slug)
        base_caption = preset.prompt_template if preset else channel.prompt_template

        # mood指定でClaude API生成済みのcaptionがある場合はそれを使用
        caption = generated_caption or request.caption or base_caption
        if request.caption and preset and not generated_caption:
            caption = f"{request.caption}, {preset.prompt_template}"

        lyrics = generated_lyrics or request.lyrics

        bpm = request.bpm
        if bpm is None and preset:
            bpm = random.randint(preset.bpm_min, preset.bpm_max)
        elif bpm is None:
            bpm = random.randint(channel.default_bpm_min, channel.default_bpm_max)

        duration = request.duration or (preset.duration if preset else channel.default_duration)
        key = request.music_key or (preset.default_key if preset else channel.default_key)
        instrumental = preset.instrumental if preset else channel.default_instrumental
        vocal_language = preset.vocal_language if preset else channel.vocal_language

        return GenerationParams(
            caption=caption,
            lyrics=lyrics,
            instrumental=instrumental if not lyrics else False,
            bpm=bpm,
            duration=duration,
            key=key,
            vocal_language=vocal_language,
        )

    async def process_request(self, session: AsyncSession, request: Request) -> Track:
        channel = await session.get(Channel, request.channel_id)
        if channel is None:
            raise ValueError(f"Channel {request.channel_id} not found")

        # mood指定時: Claude APIで曲名・キャプション・歌詞を生成
        title = None
        generated_caption = ""
        generated_lyrics = ""
        if request.mood and not request.caption and not request.lyrics and self.lyrics_generator:
            title, generated_caption, generated_lyrics = self.generate_lyrics(
                request, channel,
            )
            logger.info("Claude API 生成完了: title='%s'", title)

        params = self.build_generation_params(
            request, channel,
            generated_caption=generated_caption,
            generated_lyrics=generated_lyrics,
        )
        logger.info(
            "Generating track for channel=%s caption='%s' bpm=%s duration=%s",
            channel.slug,
            params.caption[:80],
            params.bpm,
            params.duration,
        )

        result = await self.client.generate(params)

        channel_dir = self.tracks_dir / channel.slug
        channel_dir.mkdir(parents=True, exist_ok=True)
        track_id = uuid.uuid4()
        file_path = f"{channel.slug}/{track_id}.flac"
        full_path = self.tracks_dir / file_path
        full_path.write_bytes(result.audio_data)
        file_size = os.path.getsize(full_path)

        track = Track(
            id=track_id,
            request_id=request.id,
            channel_id=channel.id,
            file_path=file_path,
            file_size=file_size,
            duration_ms=result.duration_ms,
            sample_rate=result.sample_rate,
            title=title,
            mood=request.mood,
            caption=params.caption,
            lyrics=params.lyrics,
            bpm=params.bpm,
            music_key=params.key,
            instrumental=params.instrumental,
            num_steps=params.num_steps,
            cfg_scale=params.cfg_scale,
            seed=result.seed,
        )
        session.add(track)

        await session.execute(
            update(Request)
            .where(Request.id == request.id)
            .values(
                status="completed",
                completed_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
        logger.info("Track generated: %s (%d bytes)", file_path, file_size)
        return track

    async def fail_request(self, session: AsyncSession, request_id, error_msg: str):
        await session.execute(
            update(Request)
            .where(Request.id == request_id)
            .values(
                status="failed",
                error_message=error_msg,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    async def poll_once(self) -> bool:
        async with self.session_factory() as session:
            request = await self.claim_request(session)
            if request is None:
                return False
            try:
                await self.process_request(session, request)
                return True
            except GenerationError as e:
                logger.error("Generation failed for request %s: %s", request.id, e)
                await self.fail_request(session, request.id, str(e))
                return True
            except Exception as e:
                logger.exception("Unexpected error processing request %s", request.id)
                await self.fail_request(session, request.id, str(e))
                return True

    async def _run_periodic_jobs(self):
        """棚卸し・プレイリスト更新の定期ジョブを実行"""
        async with self.session_factory() as session:
            # アクティブなチャンネルを取得
            result = await session.execute(
                select(Channel).where(Channel.is_active.is_(True))
            )
            channels = result.scalars().all()

            for channel in channels:
                # トラック数が5件未満の場合はスキップ
                count_result = await session.execute(
                    select(func.count(Track.id)).where(
                        Track.channel_id == channel.id,
                        Track.is_retired.is_(False),
                    )
                )
                track_count = count_result.scalar() or 0
                if track_count < 5:
                    continue

                now = datetime.now(timezone.utc)

                # 棚卸し（10分間隔）
                if (
                    now.timestamp() - self._last_retirement.timestamp()
                    >= self.RETIREMENT_INTERVAL
                ):
                    try:
                        await retire_unpopular_tracks(session, channel.id)
                    except Exception:
                        logger.exception("棚卸しエラー: チャンネル %s", channel.slug)

                # プレイリスト更新（5分間隔）
                if (
                    now.timestamp() - self._last_playlist.timestamp()
                    >= self.PLAYLIST_INTERVAL
                ):
                    try:
                        await generate_weighted_playlist(
                            session, channel.id, channel.slug
                        )
                    except Exception:
                        logger.exception(
                            "プレイリスト生成エラー: チャンネル %s", channel.slug
                        )

            now = datetime.now(timezone.utc)
            if (
                now.timestamp() - self._last_retirement.timestamp()
                >= self.RETIREMENT_INTERVAL
            ):
                self._last_retirement = now
            if (
                now.timestamp() - self._last_playlist.timestamp()
                >= self.PLAYLIST_INTERVAL
            ):
                self._last_playlist = now

    # 定期ジョブの間隔（秒）
    PLAYLIST_INTERVAL = 5 * 60   # 5分
    RETIREMENT_INTERVAL = 10 * 60  # 10分

    async def run(self):
        logger.info(
            "Worker %s starting poll loop (interval=%.1fs)",
            self.worker_id, settings.poll_interval,
        )
        self._last_playlist = datetime.now(timezone.utc)
        self._last_retirement = datetime.now(timezone.utc)

        while True:
            try:
                had_work = await self.poll_once()
                if not had_work:
                    await asyncio.sleep(settings.poll_interval)

                # 定期ジョブの実行チェック
                await self._run_periodic_jobs()
            except Exception:
                logger.exception("Error in poll loop")
                await asyncio.sleep(settings.poll_interval)
