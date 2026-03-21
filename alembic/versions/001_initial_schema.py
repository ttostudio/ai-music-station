"""Initial schema: channels, requests, tracks, now_playing

Revision ID: 001
Revises:
Create Date: 2026-03-21

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("default_bpm_min", sa.Integer(), server_default=sa.text("80"), nullable=False),
        sa.Column("default_bpm_max", sa.Integer(), server_default=sa.text("120"), nullable=False),
        sa.Column("default_duration", sa.Integer(), server_default=sa.text("180"), nullable=False),
        sa.Column("default_key", sa.String(10), nullable=True),
        sa.Column(
            "default_instrumental", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("vocal_language", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "requests",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column(
            "status", sa.String(20), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("music_key", sa.String(10), nullable=True),
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_requests_pending",
        "requests",
        ["status", "created_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index("idx_requests_channel", "requests", ["channel_id", "status"])

    op.create_table(
        "tracks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("request_id", sa.UUID(), nullable=True),
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), server_default=sa.text("48000"), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("music_key", sa.String(10), nullable=True),
        sa.Column("instrumental", sa.Boolean(), nullable=True),
        sa.Column("num_steps", sa.Integer(), nullable=True),
        sa.Column("cfg_scale", sa.Float(), nullable=True),
        sa.Column("seed", sa.BigInteger(), nullable=True),
        sa.Column("play_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"]),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("idx_tracks_channel", "tracks", ["channel_id", sa.text("created_at DESC")])

    op.create_table(
        "now_playing",
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("channel_id"),
    )


def downgrade() -> None:
    op.drop_table("now_playing")
    op.drop_index("idx_tracks_channel", table_name="tracks")
    op.drop_table("tracks")
    op.drop_index("idx_requests_channel", table_name="requests")
    op.drop_index("idx_requests_pending", table_name="requests")
    op.drop_table("requests")
    op.drop_table("channels")
