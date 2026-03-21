import uuid

import pytest

from worker.channel_presets import PRESETS
from worker.models import Channel, Request


@pytest.fixture
def sample_channel() -> Channel:
    preset = PRESETS["lofi"]
    return Channel(
        id=uuid.uuid4(),
        slug="lofi",
        name=preset.name,
        description=preset.description,
        is_active=True,
        default_bpm_min=preset.bpm_min,
        default_bpm_max=preset.bpm_max,
        default_duration=preset.duration,
        default_key=preset.default_key,
        default_instrumental=preset.instrumental,
        prompt_template=preset.prompt_template,
        vocal_language=preset.vocal_language,
    )


@pytest.fixture
def sample_request(sample_channel: Channel) -> Request:
    return Request(
        id=uuid.uuid4(),
        channel_id=sample_channel.id,
        status="pending",
        caption=None,
        lyrics=None,
        bpm=None,
        duration=None,
        music_key=None,
    )
