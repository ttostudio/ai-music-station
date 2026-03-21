"""Seed default channels: lofi, anime, jazz

Revision ID: 002
Revises: 001
Create Date: 2026-03-21

"""
from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO channels (slug, name, description, is_active,
            default_bpm_min, default_bpm_max, default_duration,
            default_key, default_instrumental, prompt_template, vocal_language)
        VALUES
            ('lofi', 'LoFi Beats',
             'Chill lo-fi hip hop beats to relax and study to',
             true, 70, 90, 180, 'Cm', true,
             'lo-fi hip hop beat, chill, relaxed, vinyl crackle, mellow piano, '
             || 'ambient pads, soft drums, warm bass, nostalgic, cozy atmosphere',
             NULL),
            ('anime', 'Anime Songs',
             'AI-generated anime opening and ending themes',
             true, 120, 160, 90, 'C', false,
             'anime opening theme, energetic, J-pop, catchy melody, '
             || 'orchestral arrangement, electric guitar, powerful vocals, '
             || 'dramatic, uplifting, epic chorus',
             'ja'),
            ('jazz', 'Jazz Station',
             'Smooth jazz, improvisation, and classic vibes',
             true, 100, 140, 240, NULL, true,
             'jazz, smooth, saxophone solo, piano comping, upright bass walking, '
             || 'brush drums, improvisational, warm tone, sophisticated harmony, '
             || 'swing feel, late night jazz club atmosphere',
             NULL)
        ON CONFLICT (slug) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM channels WHERE slug IN ('lofi', 'anime', 'jazz');"
    )
