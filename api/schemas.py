from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --- Channel ---

class NowPlayingInfo(BaseModel):
    track_id: uuid.UUID
    caption: str
    started_at: datetime


class ChannelResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    is_active: bool
    queue_depth: int = 0
    total_tracks: int = 0
    stream_url: str
    now_playing: NowPlayingInfo | None = None


class ChannelDetailResponse(ChannelResponse):
    default_bpm_min: int
    default_bpm_max: int
    min_duration: int
    max_duration: int
    default_instrumental: bool


class ChannelListResponse(BaseModel):
    channels: list[ChannelResponse]


# --- Request ---

class CreateRequestBody(BaseModel):
    mood: str | None = Field(None, max_length=500)
    caption: str | None = Field(None, max_length=1000)
    lyrics: str | None = Field(None, max_length=5000)
    bpm: int | None = Field(None, ge=30, le=300)
    duration: int | None = Field(None, ge=10, le=600)
    music_key: str | None = Field(None, max_length=10)


class RequestResponse(BaseModel):
    id: uuid.UUID
    channel_slug: str
    status: str
    position: int | None = None
    created_at: datetime


class RequestDetailResponse(BaseModel):
    id: uuid.UUID
    channel_slug: str
    status: str
    mood: str | None = None
    caption: str | None = None
    lyrics: str | None = None
    bpm: int | None = None
    duration: int | None = None
    music_key: str | None = None
    position: int | None = None
    vote_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    track: TrackResponse | None = None


class RequestListResponse(BaseModel):
    requests: list[RequestDetailResponse]
    total: int


# --- Track ---

class TrackResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    caption: str
    mood: str | None = None
    lyrics: str | None = None
    duration_ms: int | None = None
    bpm: int | None = None
    music_key: str | None = None
    instrumental: bool | None = None
    play_count: int = 0
    like_count: int = 0
    created_at: datetime


class TrackListResponse(BaseModel):
    tracks: list[TrackResponse]
    total: int


class TrackSearchResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    caption: str
    mood: str | None = None
    duration_ms: int | None = None
    bpm: int | None = None
    music_key: str | None = None
    instrumental: bool | None = None
    play_count: int = 0
    like_count: int = 0
    quality_score: float | None = None
    channel_slug: str
    created_at: datetime


class TrackSearchListResponse(BaseModel):
    tracks: list[TrackSearchResponse]
    total: int
    limit: int
    offset: int


class NowPlayingResponse(BaseModel):
    track: TrackResponse | None = None


# --- Reaction ---

class ReactionBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    reaction_type: Literal["like"] = "like"


class ReactionResponse(BaseModel):
    ok: bool
    count: int


class ReactionStatusResponse(BaseModel):
    count: int
    user_reacted: bool


# --- Channel Create / Full Update ---

class ChannelCreateBody(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    mood_description: str | None = None
    default_bpm_min: int = Field(80, ge=30, le=300)
    default_bpm_max: int = Field(120, ge=30, le=300)
    min_duration: int = Field(180, ge=10, le=600)
    max_duration: int = Field(600, ge=10, le=600)
    default_key: str | None = Field(None, max_length=10)
    default_instrumental: bool = True
    prompt_template: str = Field("", max_length=5000)
    vocal_language: str | None = Field(None, max_length=10)
    auto_generate: bool = True
    min_stock: int = Field(5, ge=0, le=100)
    max_stock: int = Field(50, ge=1, le=500)

    @model_validator(mode="after")
    def validate_duration_range(self) -> "ChannelCreateBody":
        if self.min_duration > self.max_duration:
            raise ValueError("min_duration は max_duration 以下にしてください")
        return self


class ChannelFullResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    mood_description: str | None
    is_active: bool
    default_bpm_min: int
    default_bpm_max: int
    min_duration: int
    max_duration: int
    default_key: str | None
    default_instrumental: bool
    prompt_template: str
    vocal_language: str | None
    auto_generate: bool
    min_stock: int
    max_stock: int


# --- Channel Partial Update ---

class ChannelUpdateBody(BaseModel):
    mood_description: str | None = Field(None, max_length=500)
    auto_generate: bool | None = None
    min_stock: int | None = Field(None, ge=1, le=100)
    max_stock: int | None = Field(None, ge=1, le=500)


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    database: str
    channels_active: int


# --- Internal ---

class NowPlayingUpdate(BaseModel):
    channel_slug: str
    track_id: uuid.UUID


class WorkerHeartbeat(BaseModel):
    worker_id: str
    active_request_id: uuid.UUID | None = None


# --- Podcast ---

class PodcastEpisodeResponse(BaseModel):
    id: uuid.UUID
    article_slug: str
    title: str
    description: str | None = None
    duration_ms: int | None = None
    episode_number: int
    status: str
    created_at: datetime


class PodcastEpisodeListResponse(BaseModel):
    episodes: list[PodcastEpisodeResponse]
    total: int


# --- Share ---

class ShareLinkResponse(BaseModel):
    share_token: str
    share_url: str
    track_id: uuid.UUID


# --- Analytics ---

class PlayEventBody(BaseModel):
    track_id: uuid.UUID
    share_token: str | None = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9_-]{0,64}$",
    )


class PlayEventResponse(BaseModel):
    ok: bool


class TrackStatsResponse(BaseModel):
    track_id: uuid.UUID
    play_count: int
    share_count: int
    like_count: int
    plays_by_source: dict[str, int]


# --- Quality Score ---

class TrackQualityResponse(BaseModel):
    track_id: uuid.UUID
    score: float
    auto_drafted: bool
    duration_sec: float | None = None
    bit_rate: int | None = None
    sample_rate: int | None = None
    mean_volume_db: float | None = None
    max_volume_db: float | None = None
    silence_ratio: float | None = None
    dynamic_range_db: float | None = None
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    scored_at: datetime


class ChannelQualityStatsResponse(BaseModel):
    channel_slug: str
    threshold: float
    total_scored: int
    avg_score: float
    auto_drafted_count: int
    score_distribution: dict[str, int]
    recent_scores: list[TrackQualityResponse]


class QualityThresholdUpdateRequest(BaseModel):
    threshold: float = Field(..., ge=0, le=100)


class QualityThresholdUpdateResponse(BaseModel):
    channel_slug: str
    threshold: float


class QualityScoreListResponse(BaseModel):
    total: int
    avg_score: float
    auto_drafted_count: int
    items: list[TrackQualityResponse]


# --- Generate status ---

class GenerateStatusResponse(BaseModel):
    channel_slug: str
    stock_count: int
    pending_count: int
    processing_count: int
    min_stock: int
    max_stock: int
    auto_generate: bool


class GenerateRequestBody(BaseModel):
    channel_slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')
    mood: str | None = Field(None, max_length=500)
    caption: str | None = Field(None, max_length=1000)
    lyrics: str | None = Field(None, max_length=5000)
    bpm: int | None = Field(None, ge=30, le=300)
    duration: int | None = Field(None, ge=10, le=600)
    music_key: str | None = Field(None, max_length=10)


# --- Playlist ---

class PlaylistCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=2048)


class PlaylistUpdateBody(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=2048)


class PlaylistSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    track_count: int
    created_at: datetime
    updated_at: datetime


class PlaylistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    track_count: int
    created_at: datetime
    updated_at: datetime


class PlaylistTrackInfo(BaseModel):
    id: uuid.UUID
    title: str | None = None
    mood: str | None = None
    caption: str
    duration_ms: int | None = None
    bpm: int | None = None
    music_key: str | None = None
    play_count: int = 0
    like_count: int = 0
    quality_score: float | None = None
    channel_id: uuid.UUID
    created_at: datetime


class PlaylistTrackEntry(BaseModel):
    position: int
    added_at: datetime
    track: PlaylistTrackInfo


class PlaylistDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    track_count: int
    created_at: datetime
    updated_at: datetime
    tracks: list[PlaylistTrackEntry]


class PlaylistListResponse(BaseModel):
    playlists: list[PlaylistSummaryResponse]
    total: int
    limit: int
    offset: int


class AddTrackBody(BaseModel):
    track_ids: list[uuid.UUID] = Field(..., min_length=1)


class AddTrackResult(BaseModel):
    track_id: uuid.UUID
    position: int
    added_at: datetime


class AddTracksResponse(BaseModel):
    playlist_id: uuid.UUID
    added: list[AddTrackResult]


class ReorderTracksBody(BaseModel):
    track_ids: list[uuid.UUID]


class ReorderTracksResponse(BaseModel):
    ok: bool


# --- Request Vote ---

class RequestVoteBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)


class RequestVoteResponse(BaseModel):
    ok: bool
    count: int


class RequestVoteStatusResponse(BaseModel):
    count: int
    user_voted: bool


# --- Channel Ranking ---

class RankingTrackResponse(BaseModel):
    rank: int
    id: uuid.UUID
    title: str | None = None
    caption: str
    like_count: int
    play_count: int
    duration_ms: int | None = None
    bpm: int | None = None


class ChannelRankingResponse(BaseModel):
    channel_slug: str
    tracks: list[RankingTrackResponse]


class FavoriteTrackInfo(BaseModel):
    id: uuid.UUID
    title: str | None = None
    mood: str | None = None
    duration_ms: int | None = None
    bpm: int | None = None
    like_count: int = 0
    quality_score: float | None = None
    channel_id: uuid.UUID
    liked_at: datetime


class FavoritesResponse(BaseModel):
    tracks: list[FavoriteTrackInfo]
    total: int
    limit: int
    offset: int


# Forward ref update
RequestDetailResponse.model_rebuild()
