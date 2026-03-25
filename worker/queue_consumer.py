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

from api.services.acestep_client import (
    AceStepClient,
    AceStepError,
    AceStepQueueFullError,
    AceStepTimeoutError,
    sanitize_bpm,
    sanitize_duration,
    sanitize_lyrics,
    sanitize_music_key,
    sanitize_prompt,
    sanitize_vocal_language,
)
from worker.acestep_client import GenerationError, GenerationParams, GenerationTimeoutError
from worker.auto_generator import run_auto_generation
from worker.channel_presets import get_preset
from worker.config import settings
from worker.models import Channel, Request, Track
from worker.playlist_generator import generate_weighted_playlist
from worker.quality_scorer import QualityScorer
from worker.track_retirement import retire_unpopular_tracks

logger = logging.getLogger(__name__)


def _split_title_caption(caption: str | None) -> tuple[str | None, str | None]:
    """キャプションからタイトルを分離する（'title | caption' 形式）"""
    if caption and " | " in caption:
        title, rest = caption.split(" | ", 1)
        return title.strip(), rest.strip()
    return None, caption


class QueueConsumer:
    def __init__(
        self,
        session_factory,
        client: AceStepClient | None = None,
        tracks_dir: str = settings.generated_tracks_dir,
        worker_id: str | None = None,
    ):
        self.session_factory = session_factory
        self.client = client or AceStepClient(
            base_url=settings.acestep_api_url,
            timeout=settings.acestep_timeout,
        )
        self.tracks_dir = Path(tracks_dir)
        self.worker_id = worker_id or settings.worker_id or platform.node()
        self.quality_scorer = QualityScorer()

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

    def build_generation_params(self, request: Request, channel: Channel) -> GenerationParams:
        preset = get_preset(channel.slug)
        base_caption = preset.prompt_template if preset else channel.prompt_template

        _, clean_caption = _split_title_caption(request.caption)
        caption = clean_caption or base_caption
        if clean_caption and preset:
            caption = f"{clean_caption}, {preset.prompt_template}"

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
            lyrics=request.lyrics,
            instrumental=instrumental if not request.lyrics else False,
            bpm=bpm,
            duration=duration,
            key=key,
            vocal_language=vocal_language,
        )

    def _build_acestep_params(self, params: GenerationParams) -> dict:
        """GenerationParams を ACE-Step POST /release_task のリクエスト dict に変換する。"""
        return {
            "prompt": sanitize_prompt(params.caption),
            "lyrics": sanitize_lyrics(params.lyrics or ""),
            "bpm": sanitize_bpm(params.bpm),
            "key_scale": sanitize_music_key(params.key) or "",
            "audio_duration": sanitize_duration(params.duration) or 180.0,
            "vocal_language": sanitize_vocal_language(params.vocal_language),
            "inference_steps": params.num_steps,
            "guidance_scale": params.cfg_scale,
            "use_random_seed": params.seed is None,
            "audio_format": "mp3",
            "task_type": "text2music",
            "thinking": False,
        }

    async def process_request(self, session: AsyncSession, request: Request) -> Track:
        channel = await session.get(Channel, request.channel_id)
        if channel is None:
            raise ValueError(f"Channel {request.channel_id} not found")

        params = self.build_generation_params(request, channel)
        acestep_params = self._build_acestep_params(params)

        logger.info(
            "Generating track for channel=%s caption='%s' bpm=%s duration=%s",
            channel.slug,
            params.caption[:80],
            params.bpm,
            params.duration,
        )

        # --- 同期生成（/v1/chat/completions） ---
        # submit_job + poll + download を1ステップに統合
        channel_dir = self.tracks_dir / channel.slug
        channel_dir.mkdir(parents=True, exist_ok=True)
        track_id = uuid.uuid4()
        file_path = f"{channel.slug}/{track_id}.mp3"
        full_path = self.tracks_dir / file_path

        await session.execute(
            update(Request)
            .where(Request.id == request.id)
            .values(
                ace_step_submitted_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        logger.info("ACE-Step sync generation started: request_id=%s", request.id)

        result = await self.client.generate_sync(acestep_params, full_path)
        file_size = full_path.stat().st_size
        logger.info("Audio generated: %s (%d bytes)", file_path, file_size)

        # duration / bpm / key をレスポンスまたは入力から取得
        duration_ms = int((result.duration or params.duration) * 1000)
        bpm = result.bpm or params.bpm
        music_key = result.key_scale or params.key

        # キャプションからタイトルを抽出
        title, _ = _split_title_caption(request.caption)
        if not title:
            title = request.mood

        track = Track(
            id=track_id,
            request_id=request.id,
            channel_id=channel.id,
            file_path=file_path,
            file_size=file_size,
            duration_ms=duration_ms,
            sample_rate=44100,
            title=title,
            mood=request.mood,
            caption=params.caption,
            lyrics=params.lyrics,
            bpm=bpm,
            music_key=music_key,
            instrumental=params.instrumental,
            num_steps=params.num_steps,
            cfg_scale=params.cfg_scale,
            seed=params.seed,
            generation_model="acestep-v15-turbo",
            ace_step_job_id=None,  # 同期生成方式では job_id なし
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

        # 品質スコアリング（fire-and-forget）
        try:
            threshold = channel.quality_threshold if hasattr(channel, "quality_threshold") else 30.0
            await self.quality_scorer.score_track(
                session=session,
                track_id=track.id,
                file_path=str(full_path),
                channel_threshold=threshold,
            )
            await session.commit()
        except Exception as exc:
            logger.warning("Quality scoring failed for track %s: %s", track.id, exc)

        return track

    async def _submit_with_retry(self, params: dict) -> str:
        """ACE-Step へのジョブ投入を指数バックオフでリトライする。"""
        backoff_seconds = [5.0, 15.0, 45.0]
        last_error: Exception | None = None
        for attempt, wait in enumerate([0.0] + backoff_seconds):
            if wait:
                await asyncio.sleep(wait)
            try:
                return await self.client.submit_job(params)
            except AceStepQueueFullError:
                # キュー満杯は 30 秒待機して最大 5 回リトライ
                if attempt < 5:
                    await asyncio.sleep(30.0)
                    try:
                        return await self.client.submit_job(params)
                    except AceStepQueueFullError as exc:
                        last_error = exc
                        continue
            except AceStepError as exc:
                last_error = exc
                continue

        raise GenerationError(
            f"ACE-Step ジョブ投入失敗（{len(backoff_seconds) + 1} 回試行）: {last_error}"
        )

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
            except (GenerationError, AceStepError) as exc:
                logger.error("Generation failed for request %s: %s", request.id, exc)
                await self.fail_request(session, request.id, str(exc))
                return True
            except Exception as exc:
                logger.exception("Unexpected error processing request %s", request.id)
                await self.fail_request(session, request.id, str(exc))
                return True

    async def _get_active_channels(self, session: AsyncSession) -> list[Channel]:
        """アクティブチャンネル一覧を取得する。"""
        result = await session.execute(
            select(Channel).where(Channel.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def _run_playlist_update(self):
        """全チャンネルのプレイリストを更新する。"""
        async with self.session_factory() as session:
            channels = await self._get_active_channels(session)
            for ch in channels:
                count_result = await session.execute(
                    select(func.count(Track.id)).where(
                        Track.channel_id == ch.id,
                        Track.is_retired == False,  # noqa: E712
                    )
                )
                track_count = count_result.scalar() or 0
                if track_count < 5:
                    continue
                await generate_weighted_playlist(
                    session, ch.id, ch.slug, str(self.tracks_dir),
                    playlist_tracks_dir=settings.liquidsoap_tracks_dir,
                )

    async def _run_track_retirement(self):
        """全チャンネルの棚卸しを実行する。"""
        async with self.session_factory() as session:
            channels = await self._get_active_channels(session)
            for ch in channels:
                count_result = await session.execute(
                    select(func.count(Track.id)).where(
                        Track.channel_id == ch.id,
                    )
                )
                track_count = count_result.scalar() or 0
                if track_count < 5:
                    continue
                await retire_unpopular_tracks(session, ch.id)

    async def run(self):
        logger.info(
            "Worker %s starting poll loop (interval=%.1fs)",
            self.worker_id, settings.poll_interval,
        )
        playlist_interval = 5 * 60   # 5分
        retirement_interval = 10 * 60  # 10分
        auto_gen_interval = 60         # 60秒
        last_playlist_update = 0.0
        last_retirement_run = 0.0
        last_auto_gen_run = 0.0

        while True:
            try:
                now = asyncio.get_event_loop().time()

                if now - last_playlist_update >= playlist_interval:
                    try:
                        await self._run_playlist_update()
                    except Exception:
                        logger.exception("プレイリスト更新エラー")
                    last_playlist_update = now

                if now - last_retirement_run >= retirement_interval:
                    try:
                        await self._run_track_retirement()
                    except Exception:
                        logger.exception("棚卸しエラー")
                    last_retirement_run = now

                if now - last_auto_gen_run >= auto_gen_interval:
                    try:
                        await run_auto_generation(self.session_factory)
                    except Exception:
                        logger.exception("自動生成エラー")
                    last_auto_gen_run = now

                had_work = await self.poll_once()
                if not had_work:
                    await asyncio.sleep(settings.poll_interval)
            except Exception:
                logger.exception("Error in poll loop")
                await asyncio.sleep(settings.poll_interval)
