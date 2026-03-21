from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelPreset:
    slug: str
    name: str
    description: str
    bpm_min: int
    bpm_max: int
    duration: int
    default_key: str | None
    instrumental: bool
    vocal_language: str | None
    prompt_template: str


PRESETS: dict[str, ChannelPreset] = {
    "lofi": ChannelPreset(
        slug="lofi",
        name="LoFi Beats",
        description="Chill lo-fi hip hop beats to relax and study to",
        bpm_min=70,
        bpm_max=90,
        duration=180,
        default_key="Cm",
        instrumental=True,
        vocal_language=None,
        prompt_template=(
            "lo-fi hip hop beat, chill, relaxed, vinyl crackle, mellow piano, "
            "ambient pads, soft drums, warm bass, nostalgic, cozy atmosphere"
        ),
    ),
    "anime": ChannelPreset(
        slug="anime",
        name="Anime Songs",
        description="AI-generated anime opening and ending themes",
        bpm_min=120,
        bpm_max=160,
        duration=90,
        default_key="C",
        instrumental=False,
        vocal_language="ja",
        prompt_template=(
            "anime opening theme, energetic, J-pop, catchy melody, "
            "orchestral arrangement, electric guitar, powerful vocals, "
            "dramatic, uplifting, epic chorus"
        ),
    ),
    "jazz": ChannelPreset(
        slug="jazz",
        name="Jazz Station",
        description="Smooth jazz, improvisation, and classic vibes",
        bpm_min=100,
        bpm_max=140,
        duration=240,
        default_key=None,
        instrumental=True,
        vocal_language=None,
        prompt_template=(
            "jazz, smooth, saxophone solo, piano comping, upright bass walking, "
            "brush drums, improvisational, warm tone, sophisticated harmony, "
            "swing feel, late night jazz club atmosphere"
        ),
    ),
}


def get_preset(slug: str) -> ChannelPreset | None:
    return PRESETS.get(slug)


def all_presets() -> list[ChannelPreset]:
    return list(PRESETS.values())
