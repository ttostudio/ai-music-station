from __future__ import annotations

import uuid
from datetime import datetime

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
    caption: str
    duration_ms: int | None = None
    bpm: int | None = None
    music_key: str | None = None
    instrumental: bool | None = None
    play_count: int = 0
    created_at: datetime


class TrackListResponse(BaseModel):
    tracks: list[TrackResponse]
    total: int


class NowPlayingResponse(BaseModel):
    track: TrackResponse | None = None


# --- Reaction ---

class ReactionBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    reaction_type: str = Field("like", max_length=20)


class ReactionResponse(BaseModel):
    ok: bool
    count: int


class ReactionStatusResponse(BaseModel):
    count: int
    user_reacted: bool


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


# Forward ref update
RequestDetailResponse.model_rebuild()
