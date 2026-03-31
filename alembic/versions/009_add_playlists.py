"""add playlists and playlist_tracks tables

Revision ID: 009
Revises: 008
Create Date: 2026-03-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("session_id", sa.String(100)),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_playlists_session_created", "playlists", ["session_id", "created_at"])
    op.create_index("idx_playlists_public_created", "playlists", ["is_public", "created_at"])

    op.create_table(
        "playlist_tracks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "playlist_id",
            UUID(as_uuid=True),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "track_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("position >= 0", name="ck_playlist_tracks_position"),
        sa.UniqueConstraint(
            "playlist_id", "track_id", name="uq_playlist_tracks_playlist_track"
        ),
    )
    op.create_index(
        "idx_playlist_tracks_playlist_pos", "playlist_tracks", ["playlist_id", "position"]
    )
    op.create_index("idx_playlist_tracks_track", "playlist_tracks", ["track_id"])


def downgrade() -> None:
    op.drop_index("idx_playlist_tracks_track", table_name="playlist_tracks")
    op.drop_index("idx_playlist_tracks_playlist_pos", table_name="playlist_tracks")
    op.drop_table("playlist_tracks")
    op.drop_index("idx_playlists_public_created", table_name="playlists")
    op.drop_index("idx_playlists_session_created", table_name="playlists")
    op.drop_table("playlists")
