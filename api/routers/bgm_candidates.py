"""BGMシーン自動マッチング用エンドポイント (#924)

GET  /api/tracks/bgm-candidates  — シーンタグでBGM候補取得
GET  /api/tracks/scene-tags      — シーンタグ付き楽曲一覧
POST /api/tracks/{track_id}/scene-tags — 楽曲にシーンタグ付与
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.db import get_session
from worker.models import Track, TrackSceneTag

router = APIRouter(prefix="/api/tracks", tags=["bgm-candidates"])

# タグ値の定義
VALID_SCENE_TYPES = frozenset(
    ["daily", "battle", "mystery", "romance", "sad", "triumph", "horror", "exploration", "ending"]
)
VALID_EMOTIONS = frozenset(
    ["happy", "melancholy", "tense", "calm", "excited", "fearful", "hopeful", "bitter"]
)
VALID_TEMPO_FEELS = frozenset(["slow", "medium", "fast"])
VALID_GENRE_FEELS = frozenset(
    ["orchestral", "piano", "electronic", "ambient", "acoustic", "epic"]
)

VALID_TAG_VALUES: dict[str, frozenset[str]] = {
    "scene_type": VALID_SCENE_TYPES,
    "emotion": VALID_EMOTIONS,
    "tempo_feel": VALID_TEMPO_FEELS,
    "genre_feel": VALID_GENRE_FEELS,
}

VALID_TAG_TYPES = frozenset(VALID_TAG_VALUES.keys())


def _stream_url(track: Track) -> str:
    """楽曲のストリームURLを生成する"""
    return f"/api/tracks/{track.id}/audio"


# --- スキーマ ---

class SceneTagResponse(BaseModel):
    tag_type: str
    tag_value: str
    confidence: float
    source: str


class TrackBgmResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    mood: str | None = None
    bpm: int | None = None
    music_key: str | None = None
    instrumental: bool | None = None
    duration_ms: int | None = None
    quality_score: float | None = None
    audio_url: str


class BgmCandidateItem(BaseModel):
    track: TrackBgmResponse
    matched_tags: list[str]
    tag_match_score: float


class BgmCandidatesResponse(BaseModel):
    candidates: list[BgmCandidateItem]
    total: int
    limit: int
    offset: int


class TrackWithSceneTagsResponse(BaseModel):
    track_id: uuid.UUID
    title: str | None = None
    bpm: int | None = None
    duration_ms: int | None = None
    quality_score: float | None = None
    audio_url: str
    scene_tags: list[SceneTagResponse]


class SceneTagsListResponse(BaseModel):
    tracks: list[TrackWithSceneTagsResponse]


class SceneTagInput(BaseModel):
    tag_type: Literal["scene_type", "emotion", "tempo_feel", "genre_feel"]
    tag_value: str = Field(..., min_length=1, max_length=64)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: Literal["manual", "auto"] = "manual"

    @field_validator("tag_value")
    @classmethod
    def validate_tag_value(cls, v: str, info: object) -> str:
        # field_validator は tag_type より後に実行されるとは限らないため
        # ここでは後でまとめてバリデーション
        return v


class AddSceneTagsBody(BaseModel):
    tags: list[SceneTagInput] = Field(..., min_length=1, max_length=20)


class AddSceneTagsResponse(BaseModel):
    track_id: uuid.UUID
    tags_added: int
    tags_updated: int
    tags: list[SceneTagResponse]


# --- エンドポイント ---

@router.get("/bgm-candidates", response_model=BgmCandidatesResponse)
async def get_bgm_candidates(
    scene_type: str | None = Query(None, max_length=64),
    emotion: str | None = Query(None, max_length=64),
    tempo_feel: str | None = Query(None, max_length=64),
    genre_feel: str | None = Query(None, max_length=64),
    min_score: float = Query(0.6, ge=0.0, le=1.0),
    exclude_ids: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> BgmCandidatesResponse:
    # タグ値バリデーション
    for tag_type_name, tag_val in [
        ("scene_type", scene_type),
        ("emotion", emotion),
        ("tempo_feel", tempo_feel),
        ("genre_feel", genre_feel),
    ]:
        if tag_val is not None and tag_val not in VALID_TAG_VALUES[tag_type_name]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_tag_value",
                    "field": tag_type_name,
                    "value": tag_val,
                },
            )

    # exclude_ids パース
    excluded: list[uuid.UUID] = []
    if exclude_ids:
        for raw_id in exclude_ids.split(",")[:20]:
            try:
                excluded.append(uuid.UUID(raw_id.strip()))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "invalid_exclude_id", "value": raw_id},
                )

    # シーンタグが存在する楽曲を取得
    query = (
        select(Track)
        .options(selectinload(Track.scene_tags))
        .where(Track.is_retired.is_(False))
    )

    if min_score > 0:
        query = query.where(
            (Track.quality_score >= min_score) | (Track.quality_score.is_(None))
        )
    if excluded:
        query = query.where(Track.id.not_in(excluded))

    result = await session.execute(query)
    all_tracks = result.scalars().all()

    # タグフィルタリングとスコアリング
    def compute_score(track: Track) -> tuple[float, list[str]]:
        tag_filter = {
            "scene_type": scene_type,
            "emotion": emotion,
            "tempo_feel": tempo_feel,
            "genre_feel": genre_feel,
        }
        active_filters = {k: v for k, v in tag_filter.items() if v is not None}

        if not active_filters:
            # フィルタなし: quality_score 順
            return (track.quality_score or 0.0, [])

        matched = []
        total_weight = len(active_filters)
        for tag in track.scene_tags:
            if tag.tag_type in active_filters and tag.tag_value == active_filters[tag.tag_type]:
                matched.append(tag.tag_value)

        score = (len(matched) / total_weight) * (track.quality_score or 1.0)
        return (score, matched)

    scored = []
    for track in all_tracks:
        score, matched_tags = compute_score(track)
        if score > 0 or not {k: v for k, v in {
            "scene_type": scene_type, "emotion": emotion,
            "tempo_feel": tempo_feel, "genre_feel": genre_feel,
        }.items() if v is not None}:
            scored.append((score, matched_tags, track))

    scored.sort(key=lambda x: x[0], reverse=True)
    total = len(scored)
    page = scored[offset : offset + limit]

    candidates = [
        BgmCandidateItem(
            track=TrackBgmResponse(
                id=t.id,
                title=t.title,
                mood=t.mood,
                bpm=t.bpm,
                music_key=t.music_key,
                instrumental=t.instrumental,
                duration_ms=t.duration_ms,
                quality_score=t.quality_score,
                audio_url=_stream_url(t),
            ),
            matched_tags=tags,
            tag_match_score=score,
        )
        for score, tags, t in page
    ]

    return BgmCandidatesResponse(
        candidates=candidates,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/scene-tags", response_model=SceneTagsListResponse)
async def list_tracks_with_scene_tags(
    session: AsyncSession = Depends(get_session),
) -> SceneTagsListResponse:
    """シーンタグが付与されている楽曲の一覧を返す"""
    result = await session.execute(
        select(Track)
        .options(selectinload(Track.scene_tags))
        .where(Track.is_retired.is_(False))
        .where(
            select(TrackSceneTag.id)
            .where(TrackSceneTag.track_id == Track.id)
            .exists()
        )
        .order_by(Track.created_at.desc())
    )
    tracks = result.scalars().all()

    return SceneTagsListResponse(
        tracks=[
            TrackWithSceneTagsResponse(
                track_id=t.id,
                title=t.title,
                bpm=t.bpm,
                duration_ms=t.duration_ms,
                quality_score=t.quality_score,
                audio_url=_stream_url(t),
                scene_tags=[
                    SceneTagResponse(
                        tag_type=tag.tag_type,
                        tag_value=tag.tag_value,
                        confidence=tag.confidence,
                        source=tag.source,
                    )
                    for tag in t.scene_tags
                ],
            )
            for t in tracks
        ]
    )


@router.post("/{track_id}/scene-tags", response_model=AddSceneTagsResponse)
async def add_scene_tags(
    track_id: uuid.UUID,
    body: AddSceneTagsBody,
    session: AsyncSession = Depends(get_session),
) -> AddSceneTagsResponse:
    """楽曲にシーンタグを付与する（upsert）"""
    # 楽曲存在確認
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(
            status_code=404,
            detail={"error": "track_not_found", "track_id": str(track_id)},
        )

    # タグ値バリデーション
    for i, tag_input in enumerate(body.tags):
        valid_vals = VALID_TAG_VALUES.get(tag_input.tag_type, frozenset())
        if tag_input.tag_value not in valid_vals:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_tag_value",
                    "field": f"tags[{i}].tag_value",
                    "value": tag_input.tag_value,
                },
            )

    # 既存タグを取得
    existing_result = await session.execute(
        select(TrackSceneTag).where(TrackSceneTag.track_id == track_id)
    )
    existing_tags = {
        (tag.tag_type, tag.tag_value): tag
        for tag in existing_result.scalars().all()
    }

    added = 0
    updated = 0

    for tag_input in body.tags:
        key = (tag_input.tag_type, tag_input.tag_value)
        if key in existing_tags:
            # 既存タグを更新
            existing = existing_tags[key]
            existing.confidence = tag_input.confidence
            existing.source = tag_input.source
            updated += 1
        else:
            # 新規追加
            new_tag = TrackSceneTag(
                track_id=track_id,
                tag_type=tag_input.tag_type,
                tag_value=tag_input.tag_value,
                confidence=tag_input.confidence,
                source=tag_input.source,
            )
            session.add(new_tag)
            added += 1

    await session.commit()

    # 最新タグを再取得
    refresh_result = await session.execute(
        select(TrackSceneTag).where(TrackSceneTag.track_id == track_id)
    )
    final_tags = refresh_result.scalars().all()

    return AddSceneTagsResponse(
        track_id=track_id,
        tags_added=added,
        tags_updated=updated,
        tags=[
            SceneTagResponse(
                tag_type=t.tag_type,
                tag_value=t.tag_value,
                confidence=t.confidence,
                source=t.source,
            )
            for t in final_tags
        ],
    )
