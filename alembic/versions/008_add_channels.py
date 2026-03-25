"""Add channels: classical, electronic, bossanova

Revision ID: 008
Revises: 007
Create Date: 2026-03-25

"""
from collections.abc import Sequence

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO channels (slug, name, description, is_active,
            default_bpm_min, default_bpm_max, default_duration,
            default_key, default_instrumental, prompt_template, vocal_language)
        VALUES
            ('classical', 'クラシック',
             'ピアノ・オーケストラの優雅なクラシック音楽',
             true, 60, 120, 300, NULL, true,
             'classical music, orchestral, piano, strings, elegant, sophisticated, '
             || 'concert hall acoustics, dynamic range, expressive, '
             || 'baroque to romantic era inspired, emotional depth',
             NULL),
            ('electronic', 'エレクトロニカ',
             '実験的なエレクトロニクスとアンビエントサウンド',
             true, 110, 150, 180, NULL, true,
             'electronic music, synthesizer, ambient, atmospheric, '
             || 'beat-driven, futuristic, pulsing bassline, '
             || 'layered textures, modular synth, hypnotic groove',
             NULL),
            ('bossanova', 'ボサノバ',
             'ブラジルのリズムとジャズが融合したボサノバ',
             true, 80, 110, 210, NULL, false,
             'bossa nova, Brazilian jazz, nylon guitar, soft percussion, '
             || 'warm vocals, samba rhythm, cool harmony, laid-back groove, '
             || 'summer breeze, cafe atmosphere, intimate and elegant',
             'ja')
        ON CONFLICT (slug) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM channels WHERE slug IN ('classical', 'electronic', 'bossanova');"
    )
