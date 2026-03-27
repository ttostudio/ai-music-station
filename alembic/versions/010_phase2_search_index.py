"""phase2_search_index

Revision ID: 010
Revises: 009
Create Date: 2026-03-28

"""
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_title_trgm "
        "ON tracks USING GIN (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_mood_trgm "
        "ON tracks USING GIN (mood gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_caption_trgm "
        "ON tracks USING GIN (caption gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tracks_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_tracks_mood_trgm")
    op.execute("DROP INDEX IF EXISTS idx_tracks_caption_trgm")
