"""Phase 1: スキーマ拡張 — reactions テーブル、tracks/requests/channels カラム追加

Revision ID: 003
Revises: 002
Create Date: 2026-03-21

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- requests テーブル拡張 ---
    op.add_column("requests", sa.Column("mood", sa.Text(), nullable=True))

    # --- tracks テーブル拡張 ---
    op.add_column("tracks", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("tracks", sa.Column("mood", sa.Text(), nullable=True))
    op.add_column(
        "tracks",
        sa.Column("is_retired", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "tracks",
        sa.Column("like_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )

    # --- channels テーブル拡張 ---
    op.add_column("channels", sa.Column("mood_description", sa.Text(), nullable=True))
    op.add_column(
        "channels",
        sa.Column("auto_generate", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "channels",
        sa.Column("min_stock", sa.Integer(), server_default=sa.text("5"), nullable=False),
    )
    op.add_column(
        "channels",
        sa.Column("max_stock", sa.Integer(), server_default=sa.text("50"), nullable=False),
    )

    # --- reactions テーブル新規 ---
    op.create_table(
        "reactions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("reaction_type", sa.String(20), server_default=sa.text("'like'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.UniqueConstraint("track_id", "session_id", name="uq_reactions_track_session"),
    )
    op.create_index("idx_reactions_track", "reactions", ["track_id"])


def downgrade() -> None:
    op.drop_index("idx_reactions_track", table_name="reactions")
    op.drop_table("reactions")

    op.drop_column("channels", "max_stock")
    op.drop_column("channels", "min_stock")
    op.drop_column("channels", "auto_generate")
    op.drop_column("channels", "mood_description")

    op.drop_column("tracks", "like_count")
    op.drop_column("tracks", "is_retired")
    op.drop_column("tracks", "mood")
    op.drop_column("tracks", "title")

    op.drop_column("requests", "mood")
