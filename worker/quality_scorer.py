"""トラック品質自動スコアリング

ffprobe/ffmpeg で音響特徴量を抽出し、重み付きスコアを算出する。
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models import Track, TrackQualityScore

logger = logging.getLogger(__name__)


@dataclass
class AudioFeatures:
    duration_sec: float = 0.0
    bit_rate: int = 0
    sample_rate: int = 0
    channels: int = 0
    codec_name: str = ""
    mean_volume_db: float = -100.0
    max_volume_db: float = -100.0
    silence_ratio: float = 1.0
    dynamic_range_db: float = 0.0


class QualityScorer:
    def __init__(
        self,
        ffprobe_path: str = "ffprobe",
        ffmpeg_path: str = "ffmpeg",
    ):
        self.ffprobe_path = ffprobe_path
        self.ffmpeg_path = ffmpeg_path

    async def score_track(
        self,
        session: AsyncSession,
        track_id: uuid.UUID,
        file_path: str,
        channel_threshold: float = 30.0,
    ) -> TrackQualityScore:
        features = await self._extract_features(file_path)
        features.silence_ratio = await self._detect_silence_ratio(file_path, features.duration_sec)
        features.dynamic_range_db = features.max_volume_db - features.mean_volume_db

        score, breakdown = self._calculate_score(features)

        auto_drafted = score < channel_threshold

        # 既存スコアを削除してから新規挿入（重複防止 / UPSERT相当）
        await session.execute(
            delete(TrackQualityScore).where(TrackQualityScore.track_id == track_id)
        )

        quality_record = TrackQualityScore(
            id=uuid.uuid4(),
            track_id=track_id,
            score=score,
            duration_sec=features.duration_sec,
            bit_rate=features.bit_rate,
            sample_rate=features.sample_rate,
            mean_volume_db=features.mean_volume_db,
            max_volume_db=features.max_volume_db,
            silence_ratio=features.silence_ratio,
            dynamic_range_db=features.dynamic_range_db,
            score_details=breakdown,
            auto_drafted=auto_drafted,
        )
        session.add(quality_record)

        now = datetime.now(timezone.utc)
        update_values: dict = {
            "quality_score": score,
            "quality_scored_at": now,
        }
        if auto_drafted:
            update_values["is_retired"] = True
            logger.info(
                "Auto-drafted track %s (score=%.1f < threshold=%.1f)",
                track_id, score, channel_threshold,
            )

        await session.execute(
            update(Track)
            .where(Track.id == track_id)
            .values(**update_values)
        )
        await session.flush()

        logger.info(
            "Quality scored track %s: %.1f points (auto_drafted=%s)",
            track_id, score, auto_drafted,
        )
        return quality_record

    async def _extract_features(self, file_path: str) -> AudioFeatures:
        features = AudioFeatures()

        proc = await asyncio.create_subprocess_exec(
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("ffprobe failed for %s: %s", file_path, stderr.decode())
            return features

        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            logger.warning("ffprobe returned invalid JSON for %s", file_path)
            return features

        fmt = data.get("format", {})
        features.duration_sec = float(fmt.get("duration", 0))
        features.bit_rate = int(fmt.get("bit_rate", 0))

        streams = data.get("streams", [])
        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"), {}
        )
        features.sample_rate = int(audio_stream.get("sample_rate", 0))
        features.channels = int(audio_stream.get("channels", 0))
        features.codec_name = audio_stream.get("codec_name", "")

        # 音量統計を astats で取得
        vol_proc = await asyncio.create_subprocess_exec(
            self.ffprobe_path,
            "-v", "quiet",
            "-of", "json",
            "-f", "lavfi",
            "-i", f"amovie='{file_path}',astats=metadata=1:reset=0",
            "-show_entries",
            "frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        vol_stdout, _ = await vol_proc.communicate()

        if vol_proc.returncode == 0:
            try:
                vol_data = json.loads(vol_stdout.decode())
                frames = vol_data.get("frames", [])
                if frames:
                    last_frame = frames[-1]
                    tags = last_frame.get("tags", {})
                    rms = tags.get("lavfi.astats.Overall.RMS_level")
                    peak = tags.get("lavfi.astats.Overall.Peak_level")
                    if rms is not None:
                        features.mean_volume_db = float(rms)
                    if peak is not None:
                        features.max_volume_db = float(peak)
            except (json.JSONDecodeError, ValueError, KeyError):
                logger.warning("Failed to parse volume stats for %s", file_path)

        return features

    async def _detect_silence_ratio(
        self, file_path: str, total_duration: float
    ) -> float:
        if total_duration <= 0:
            return 1.0

        proc = await asyncio.create_subprocess_exec(
            self.ffmpeg_path,
            "-i", file_path,
            "-af", "silencedetect=noise=-30dB:d=0.5",
            "-f", "null",
            "-",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        output = stderr.decode()

        silence_total = 0.0
        for match in re.finditer(
            r"silence_duration:\s*([\d.]+)", output
        ):
            silence_total += float(match.group(1))

        return min(silence_total / total_duration, 1.0)

    def _calculate_score(
        self, features: AudioFeatures
    ) -> tuple[float, dict]:
        breakdown: dict[str, float] = {}

        # duration (25点)
        d = features.duration_sec
        if d >= 60 and d <= 600:
            breakdown["duration"] = 25.0
        elif d >= 30:
            breakdown["duration"] = 15.0
        elif d >= 10:
            breakdown["duration"] = 5.0
        else:
            breakdown["duration"] = 0.0

        # mean_volume (25点)
        mv = features.mean_volume_db
        if -20 <= mv <= -6:
            breakdown["mean_volume"] = 25.0
        elif -25 <= mv < -20 or -6 < mv <= -3:
            breakdown["mean_volume"] = 18.0
        elif mv > -3:
            breakdown["mean_volume"] = 5.0
        else:
            breakdown["mean_volume"] = 0.0

        # silence_ratio (25点)
        sr = features.silence_ratio
        if sr <= 0.05:
            breakdown["silence"] = 25.0
        elif sr <= 0.15:
            breakdown["silence"] = 18.0
        elif sr <= 0.30:
            breakdown["silence"] = 10.0
        elif sr <= 0.50:
            breakdown["silence"] = 3.0
        else:
            breakdown["silence"] = 0.0

        # bit_rate + sample_rate (15点)
        br = features.bit_rate
        srate = features.sample_rate
        if br >= 192000 and srate >= 44100:
            breakdown["quality"] = 15.0
        elif br >= 128000 and srate >= 44100:
            breakdown["quality"] = 10.0
        elif br >= 64000:
            breakdown["quality"] = 5.0
        else:
            breakdown["quality"] = 0.0

        # dynamic_range (10点)
        dr = features.dynamic_range_db
        if 10 <= dr <= 30:
            breakdown["dynamics"] = 10.0
        elif 5 <= dr < 10:
            breakdown["dynamics"] = 6.0
        elif 1 <= dr < 5:
            breakdown["dynamics"] = 2.0
        else:
            breakdown["dynamics"] = 0.0

        total = sum(breakdown.values())
        return total, breakdown
