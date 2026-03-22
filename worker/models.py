import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    default_bpm_min: Mapped[int] = mapped_column(Integer, default=80)
    default_bpm_max: Mapped[int] = mapped_column(Integer, default=120)
    default_duration: Mapped[int] = mapped_column(Integer, default=180)
    default_key: Mapped[Optional[str]] = mapped_column(String(10))
    default_instrumental: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    vocal_language: Mapped[Optional[str]] = mapped_column(String(10))
    mood_description: Mapped[Optional[str]] = mapped_column(Text)
    auto_generate: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    min_stock: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    max_stock: Mapped[int] = mapped_column(Integer, default=50, server_default="50")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    requests: Mapped[List["Request"]] = relationship(back_populates="channel")
    tracks: Mapped[List["Track"]] = relationship(back_populates="channel")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    mood: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    lyrics: Mapped[Optional[str]] = mapped_column(Text)
    bpm: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    music_key: Mapped[Optional[str]] = mapped_column(String(10))
    worker_id: Mapped[Optional[str]] = mapped_column(String(100))
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="requests")
    track: Mapped[Optional["Track"]] = relationship(back_populates="request")

    __table_args__ = (
        Index(
            "idx_requests_pending",
            "status",
            "created_at",
            postgresql_where=(status == "pending"),
        ),
        Index("idx_requests_channel", "channel_id", "status"),
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id"), unique=True
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    sample_rate: Mapped[int] = mapped_column(Integer, default=48000)
    title: Mapped[Optional[str]] = mapped_column(Text)
    mood: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    lyrics: Mapped[Optional[str]] = mapped_column(Text)
    bpm: Mapped[Optional[int]] = mapped_column(Integer)
    music_key: Mapped[Optional[str]] = mapped_column(String(10))
    instrumental: Mapped[Optional[bool]] = mapped_column(Boolean)
    num_steps: Mapped[Optional[int]] = mapped_column(Integer)
    cfg_scale: Mapped[Optional[float]] = mapped_column(Float)
    seed: Mapped[Optional[int]] = mapped_column(Integer)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_retired: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_played_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    request: Mapped[Optional["Request"]] = relationship(
        back_populates="track"
    )
    channel: Mapped["Channel"] = relationship(back_populates="tracks")

    __table_args__ = (
        Index("idx_tracks_channel", "channel_id", "created_at"),
    )


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="like"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    track: Mapped["Track"] = relationship()

    __table_args__ = (
        Index("idx_reactions_track", "track_id"),
    )


class NowPlaying(Base):
    __tablename__ = "now_playing"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), primary_key=True
    )
    track_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id")
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
