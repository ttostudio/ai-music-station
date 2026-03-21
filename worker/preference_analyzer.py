"""嗜好分析 — チャンネルごとの高評価トラック傾向を分析し、生成プロンプトに反映する"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models import Track

if TYPE_CHECKING:
    import uuid


@dataclass
class PreferenceProfile:
    """チャンネルの嗜好プロファイル"""
    channel_id: uuid.UUID
    top_keywords: list[str]
    bpm_range: tuple[int, int] | None
    instrumental_ratio: float
    sample_size: int
    prompt_hint: str


def _extract_keywords(captions: list[str], top_n: int = 5) -> list[str]:
    """キャプションから頻出キーワードを抽出する"""
    word_count: dict[str, int] = {}
    stop_words = {"the", "a", "an", "and", "or", "of", "in", "to", "for", "is", "on", "with"}

    for caption in captions:
        words = caption.lower().split()
        for word in words:
            cleaned = word.strip(",.!?;:\"'()[]")
            if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
                word_count[cleaned] = word_count.get(cleaned, 0) + 1

    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def _compute_bpm_range(bpms: list[int]) -> tuple[int, int] | None:
    """BPM帯を算出する（中央50%の範囲）"""
    if not bpms:
        return None
    sorted_bpms = sorted(bpms)
    q1_idx = len(sorted_bpms) // 4
    q3_idx = (len(sorted_bpms) * 3) // 4
    return sorted_bpms[q1_idx], sorted_bpms[q3_idx]


def _build_prompt_hint(profile_keywords: list[str], bpm_range: tuple[int, int] | None) -> str:
    """嗜好プロファイルから生成プロンプトへの注入テキストを組み立てる"""
    parts: list[str] = []
    if profile_keywords:
        parts.append(f"listener-preferred elements: {', '.join(profile_keywords)}")
    if bpm_range:
        parts.append(f"preferred BPM range: {bpm_range[0]}-{bpm_range[1]}")
    return "; ".join(parts) if parts else ""


async def analyze_channel_preferences(
    session: AsyncSession,
    channel_id: uuid.UUID,
    min_likes: int = 1,
    limit: int = 50,
) -> PreferenceProfile:
    """チャンネル内の高評価トラックを分析し、嗜好プロファイルを返す

    Args:
        session: DBセッション
        channel_id: 対象チャンネルID
        min_likes: 最低いいね数の閾値
        limit: 分析対象の最大トラック数
    """
    result = await session.execute(
        select(Track)
        .where(Track.channel_id == channel_id, Track.like_count >= min_likes)
        .order_by(Track.like_count.desc())
        .limit(limit)
    )
    tracks = result.scalars().all()

    if not tracks:
        return PreferenceProfile(
            channel_id=channel_id,
            top_keywords=[],
            bpm_range=None,
            instrumental_ratio=0.0,
            sample_size=0,
            prompt_hint="",
        )

    captions = [t.caption for t in tracks if t.caption]
    bpms = [t.bpm for t in tracks if t.bpm is not None]
    instrumental_count = sum(1 for t in tracks if t.instrumental)

    keywords = _extract_keywords(captions)
    bpm_range = _compute_bpm_range(bpms)
    instrumental_ratio = instrumental_count / len(tracks)
    prompt_hint = _build_prompt_hint(keywords, bpm_range)

    return PreferenceProfile(
        channel_id=channel_id,
        top_keywords=keywords,
        bpm_range=bpm_range,
        instrumental_ratio=instrumental_ratio,
        sample_size=len(tracks),
        prompt_hint=prompt_hint,
    )
