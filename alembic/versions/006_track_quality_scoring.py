"""track_quality_scores テーブル追加 / tracks, channels にスコア関連カラム追加

Revision ID: 006
Revises: 005
Create Date: 2026-03-24

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # track_quality_scores テーブル
    op.create_table(
        "track_quality_scores",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=True),
        sa.Column("bit_rate", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("mean_volume_db", sa.Float(), nullable=True),
        sa.Column("max_volume_db", sa.Float(), nullable=True),
        sa.Column("silence_ratio", sa.Float(), nullable=True),
        sa.Column("dynamic_range_db", sa.Float(), nullable=True),
        sa.Column(
            "score_details",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "auto_drafted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["track_id"], ["tracks.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("idx_tqs_track_id", "track_quality_scores", ["track_id"])
    op.create_index("idx_tqs_score", "track_quality_scores", ["score"])
    op.create_index(
        "idx_tqs_created",
        "track_quality_scores",
        [sa.text("created_at DESC")],
    )

    # tracks テーブルにスコア関連カラム追加
    op.add_column(
        "tracks", sa.Column("quality_score", sa.Float(), nullable=True)
    )
    op.add_column(
        "tracks",
        sa.Column(
            "quality_scored_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index(
        "idx_tracks_quality_score", "tracks", ["quality_score"]
    )

    # channels テーブルに品質閾値カラム追加
    op.add_column(
        "channels",
        sa.Column(
            "quality_threshold",
            sa.Float(),
            server_default=sa.text("30.0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("channels", "quality_threshold")
    op.drop_index("idx_tracks_quality_score", table_name="tracks")
    op.drop_column("tracks", "quality_scored_at")
    op.drop_column("tracks", "quality_score")
    op.drop_index("idx_tqs_created", table_name="track_quality_scores")
    op.drop_index("idx_tqs_score", table_name="track_quality_scores")
    op.drop_index("idx_tqs_track_id", table_name="track_quality_scores")
    op.drop_table("track_quality_scores")
