from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

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
    default_duration: int
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
    default_duration: int = Field(180, ge=10, le=600)
    default_key: str | None = Field(None, max_length=10)
    default_instrumental: bool = True
    prompt_template: str = Field(..., min_length=1)
    vocal_language: str | None = Field(None, max_length=10)
    auto_generate: bool = True
    min_stock: int = Field(5, ge=0, le=100)
    max_stock: int = Field(50, ge=1, le=500)


class ChannelFullResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    mood_description: str | None
    is_active: bool
    default_bpm_min: int
    default_bpm_max: int
    default_duration: int
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


# Forward ref update
RequestDetailResponse.model_rebuild()
