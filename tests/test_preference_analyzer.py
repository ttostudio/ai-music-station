"""嗜好分析ロジックのテスト"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from worker.models import Track
from worker.preference_analyzer import (
    PreferenceProfile,
    _compute_bpm_range,
    _extract_keywords,
    analyze_channel_preferences,
)


class TestExtractKeywords:
    def test_extracts_frequent_words(self):
        captions = [
            "chill lo-fi beat with piano",
            "relaxing chill beat",
            "chill piano melody",
        ]
        keywords = _extract_keywords(captions, top_n=3)
        assert "chill" in keywords
        assert len(keywords) <= 3

    def test_filters_short_and_stop_words(self):
        captions = ["the a an and or of in to for is"]
        keywords = _extract_keywords(captions)
        assert keywords == []

    def test_empty_input(self):
        assert _extract_keywords([]) == []


class TestComputeBpmRange:
    def test_returns_quartile_range(self):
        bpms = [70, 75, 80, 85, 90, 95, 100, 105]
        result = _compute_bpm_range(bpms)
        assert result is not None
        low, high = result
        assert low == 80
        assert high == 100

    def test_returns_none_for_empty(self):
        assert _compute_bpm_range([]) is None

    def test_single_value(self):
        result = _compute_bpm_range([120])
        assert result == (120, 120)


class TestAnalyzeChannelPreferences:
    @pytest.fixture
    def channel_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def liked_tracks(self, channel_id):
        return [
            Track(
                id=uuid.uuid4(),
                channel_id=channel_id,
                file_path=f"/audio/track{i}.wav",
                caption=caption,
                bpm=bpm,
                instrumental=instrumental,
                like_count=likes,
                play_count=0,
                created_at=datetime.now(timezone.utc),
            )
            for i, (caption, bpm, instrumental, likes) in enumerate([
                ("chill lo-fi piano beat", 80, True, 5),
                ("relaxing chill ambient", 75, True, 3),
                ("energetic chill drums", 85, False, 2),
            ])
        ]

    @pytest.mark.asyncio
    async def test_analyzes_liked_tracks(self, channel_id, liked_tracks):
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = liked_tracks
        mock_session.execute = AsyncMock(return_value=result_mock)

        profile = await analyze_channel_preferences(mock_session, channel_id)

        assert isinstance(profile, PreferenceProfile)
        assert profile.channel_id == channel_id
        assert profile.sample_size == 3
        assert "chill" in profile.top_keywords
        assert profile.bpm_range is not None
        assert profile.instrumental_ratio == pytest.approx(2 / 3)
        assert profile.prompt_hint != ""

    @pytest.mark.asyncio
    async def test_returns_empty_profile_when_no_tracks(self, channel_id):
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result_mock)

        profile = await analyze_channel_preferences(mock_session, channel_id)

        assert profile.sample_size == 0
        assert profile.top_keywords == []
        assert profile.bpm_range is None
        assert profile.prompt_hint == ""
