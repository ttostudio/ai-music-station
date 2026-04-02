import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
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
    min_duration: Mapped[int] = mapped_column(Integer, default=180, server_default="180")
    max_duration: Mapped[int] = mapped_column(Integer, default=600, server_default="600")
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

    content_type: Mapped[str] = mapped_column(
        String(20), default="music", server_default="music"
    )

    quality_threshold: Mapped[float] = mapped_column(
        Float, default=30.0, server_default="30.0"
    )

    requests: Mapped[List["Request"]] = relationship(back_populates="channel")
    tracks: Mapped[List["Track"]] = relationship(back_populates="channel")
    podcast_episodes: Mapped[List["PodcastEpisode"]] = relationship(back_populates="channel")


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
    ace_step_job_id: Mapped[Optional[str]] = mapped_column(String(200))
    ace_step_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    ace_step_poll_count: Mapped[Optional[int]] = mapped_column(
        Integer, default=0
    )
    vote_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="requests")
    track: Mapped[Optional["Track"]] = relationship(back_populates="request")
    votes: Mapped[List["RequestVote"]] = relationship(back_populates="request")

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
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    quality_scored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_played_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    generation_model: Mapped[Optional[str]] = mapped_column(String(100))
    ace_step_job_id: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    request: Mapped[Optional["Request"]] = relationship(
        back_populates="track"
    )
    channel: Mapped["Channel"] = relationship(back_populates="tracks")
    scene_tags: Mapped[List["TrackSceneTag"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tracks_channel", "channel_id", "created_at"),
        Index("idx_tracks_quality_score", "quality_score"),
    )


class TrackSceneTag(Base):
    """楽曲シーン適合タグ (#924)"""

    __tablename__ = "track_scene_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    # 'scene_type' | 'emotion' | 'tempo_feel' | 'genre_feel'
    tag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_value: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, server_default="1.0")
    # 'manual' | 'auto'
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual", server_default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    track: Mapped["Track"] = relationship(back_populates="scene_tags")

    __table_args__ = (
        Index("idx_track_scene_tags_track", "track_id"),
        Index("idx_track_scene_tags_type_value", "tag_type", "tag_value"),
        UniqueConstraint("track_id", "tag_type", "tag_value", name="idx_track_scene_tags_unique"),
    )


class RequestVote(Base):
    __tablename__ = "request_votes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    request: Mapped["Request"] = relationship(back_populates="votes")

    __table_args__ = (
        UniqueConstraint("request_id", "session_id", name="uq_request_votes_request_session"),
        Index("idx_request_votes_request", "request_id"),
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


class PodcastEpisode(Base):
    __tablename__ = "podcast_episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False
    )
    article_id: Mapped[Optional[str]] = mapped_column(String(255))
    article_slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    audio_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="published", server_default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="podcast_episodes")

    __table_args__ = (
        Index("idx_podcast_episodes_channel", "channel_id", "episode_number"),
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


class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    share_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    track: Mapped["Track"] = relationship()

    __table_args__ = (
        Index("idx_share_links_token", "share_token", unique=True),
        Index("idx_share_links_track", "track_id"),
    )


class TrackAnalytics(Base):
    __tablename__ = "track_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    referer: Mapped[Optional[str]] = mapped_column(Text)
    share_token: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_track_analytics_track_created", "track_id", "created_at"),
        Index("idx_track_analytics_event_created", "event_type", "created_at"),
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_image_url: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    playlist_tracks: Mapped[List["PlaylistTrack"]] = relationship(
        back_populates="playlist",
        order_by="PlaylistTrack.position",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_playlists_session_created", "session_id", "created_at"),
        Index("idx_playlists_public_created", "is_public", "created_at"),
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    playlist: Mapped["Playlist"] = relationship(back_populates="playlist_tracks")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "playlist_id", "track_id", name="uq_playlist_tracks_playlist_track"
        ),
        Index("idx_playlist_tracks_playlist_pos", "playlist_id", "position"),
        Index("idx_playlist_tracks_track", "track_id"),
    )


class TrackQualityScore(Base):
    __tablename__ = "track_quality_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[Optional[float]] = mapped_column(Float)
    bit_rate: Mapped[Optional[int]] = mapped_column(Integer)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer)
    mean_volume_db: Mapped[Optional[float]] = mapped_column(Float)
    max_volume_db: Mapped[Optional[float]] = mapped_column(Float)
    silence_ratio: Mapped[Optional[float]] = mapped_column(Float)
    dynamic_range_db: Mapped[Optional[float]] = mapped_column(Float)
    score_details: Mapped[Optional[dict]] = mapped_column(JSON)
    auto_drafted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    track: Mapped["Track"] = relationship()

    __table_args__ = (
        Index("idx_tqs_track_id", "track_id"),
        Index("idx_tqs_score", "score"),
    )
