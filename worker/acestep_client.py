"""ACE-Step クライアント — api.services.acestep_client への互換シム。

worker パッケージは api.services.acestep_client の AceStepClient を使用する。
このモジュールは後方互換のため GenerationParams / GenerationResult を提供し、
ACEStepClient を AceStepClient のエイリアスとして再エクスポートする。
"""
from __future__ import annotations

from dataclasses import dataclass

from api.services.acestep_client import (  # noqa: F401
    AceStepClient,
    AceStepError as GenerationError,
    AceStepQueueFullError,
    AceStepTimeoutError as GenerationTimeoutError,
    sanitize_bpm,
    sanitize_duration,
    sanitize_lyrics,
    sanitize_music_key,
    sanitize_prompt,
    sanitize_vocal_language,
)

# Legacy alias: 既存コードは ACEStepClient 名でも参照できる
ACEStepClient = AceStepClient


def _build_prompt(params: "GenerationParams") -> str:
    """GenerationParams からプロンプト文字列を構築する（後方互換ヘルパー）。"""
    parts = [params.caption]
    if params.instrumental and not params.lyrics:
        parts.append("Instrumental")
    if params.bpm:
        parts.append(f"BPM: {params.bpm}")
    if params.key:
        parts.append(f"Key: {params.key}")
    if params.lyrics:
        parts.append(f"Lyrics: {params.lyrics}")
    return " ".join(parts)


@dataclass
class GenerationParams:
    """Worker → ACE-Step パラメータ転送用 DTO。"""

    caption: str
    lyrics: str | None = None
    instrumental: bool = True
    bpm: int | None = None
    duration: int = 180
    key: str | None = None
    time_signature: int | None = 4
    vocal_language: str | None = None
    num_steps: int = 8
    cfg_scale: float = 7.0
    seed: int | None = None


@dataclass
class GenerationResult:
    """Worker 内部での生成結果 DTO（後方互換）。"""

    audio_data: bytes
    sample_rate: int
    seed: int
    duration_ms: int
